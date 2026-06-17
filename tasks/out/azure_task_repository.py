from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from sd_metrics_lib.sources.azure.query import AzureSearchQueryBuilder
from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider
from sd_metrics_lib.sources.azure.worklog import AzureStatusChangeWorklogExtractor
from sd_metrics_lib.sources.story_points import FunctionStoryPointExtractor
from sd_metrics_lib.sources.tasks import CachingTaskProvider
from sd_metrics_lib.utils.worktime import WorkTimeExtractor, SIMPLE_WORKTIME_EXTRACTOR, BoundarySimpleWorkTimeExtractor

from .convertors.azure import AzureTaskConverter
from .story_point_extractors import extract_azure_story_points
from ..app.domain.model.config import TasksConfig
from ..app.domain.model.task import TaskSearchCriteria, Task, EnrichmentOptions, WorkTimeExtractorType
from ..app.spi.task_repository import TaskRepository


class AzureTaskRepository(TaskRepository):

    def __init__(self, config: TasksConfig, worktime_extractor_type: Optional[WorkTimeExtractorType] = None,
                 cache=None):
        azure_config = config.azure
        if not all([azure_config.azure_organization_url, azure_config.azure_pat]):
            raise ValueError("Missing Azure authentication configuration")

        if not config.project.project_keys:
            raise ValueError("Missing project keys configuration")

        credentials = BasicAuthentication('', azure_config.azure_pat)
        self.connection = Connection(base_url=azure_config.azure_organization_url, creds=credentials)
        self.project_keys = config.project.project_keys
        self.azure_organization_url = azure_config.azure_organization_url
        self.config = config
        self.worktime_extractor_type = worktime_extractor_type or WorkTimeExtractorType.SIMPLE
        self._executor = ThreadPoolExecutor(max_workers=100, thread_name_prefix="azure-fetch")
        self._cache = cache
        self._story_point_extractor = FunctionStoryPointExtractor(extract_azure_story_points(config))

    async def find_all(self, search_criteria: Optional[TaskSearchCriteria] = None,
                       enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        query = self._build_search_query(search_criteria)
        azure_tasks = await self._fetch_azure_tasks(query)
        converter = self._create_converter_for_criteria(search_criteria, enrichment)
        tasks = [converter.convert_to_task(azure_task) for azure_task in azure_tasks]
        self._enrich_parent_titles(tasks)
        return tasks

    def _build_search_query(self, search_criteria: Optional[TaskSearchCriteria]) -> str:
        if search_criteria is None:
            return AzureSearchQueryBuilder(projects=self.project_keys).build_query()

        sorted_assignees_history = None
        if search_criteria.assignees_history_filter:
            sorted_assignees_history = sorted(search_criteria.assignees_history_filter)

        sorted_assignees = None
        if search_criteria.assignee_filter:
            sorted_assignees = sorted(search_criteria.assignee_filter)

        raw_queries = None
        if search_criteria.raw_jql_filter:
            raw_queries = [search_criteria.raw_jql_filter]

        builder = AzureSearchQueryBuilder(
            projects=self.project_keys,
            task_types=search_criteria.type_filter,
            statuses=search_criteria.status_filter,
            teams=search_criteria.team_filter,
            assignees=sorted_assignees,
            assignees_history=sorted_assignees_history,
            task_ids=search_criteria.id_filter,
            last_modified_dates=search_criteria.last_modified_date_range,
            resolution_dates=search_criteria.resolution_date_range,
            raw_queries=raw_queries
        )

        return builder.build_query()

    async def _fetch_azure_tasks(self, query: str):
        azure_client = self.connection.clients.get_work_item_tracking_client()

        additional_fields = list(AzureTaskProvider.DEFAULT_FIELDS)
        additional_fields.extend([
            "System.ChangedDate",
            "System.TeamProject",
            "System.AreaPath",
            "System.Parent",
            "Microsoft.VSTS.Common.Priority"
        ])
        if self.config.azure.release_field:
            additional_fields.append(self.config.azure.release_field)
        additional_fields.extend(self.config.sorting.custom_sort_field_names())

        base_provider = AzureTaskProvider(
            azure_client,
            query,
            additional_fields=additional_fields,
            custom_expand_fields=[
                AzureTaskProvider.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME,
                AzureTaskProvider.CHILD_TASKS_CUSTOM_FIELD_NAME
            ],
            thread_pool_executor=self._executor,
        )

        cached_provider = CachingTaskProvider(base_provider, self._cache)
        return cached_provider.get_tasks()

    def _enrich_parent_titles(self, tasks: List[Task]) -> None:
        unresolved_parent_ids = self._collect_unresolved_parent_ids(tasks)
        if not unresolved_parent_ids:
            return

        parent_titles_by_id = self._fetch_parent_titles(unresolved_parent_ids)
        for task in tasks:
            if task.parent and not task.parent.title:
                resolved_title = parent_titles_by_id.get(task.parent.id)
                if resolved_title:
                    task.parent.title = resolved_title

    @staticmethod
    def _collect_unresolved_parent_ids(tasks: List[Task]) -> List[int]:
        unique_parent_ids = set()
        for task in tasks:
            if not task.parent or task.parent.title:
                continue
            try:
                unique_parent_ids.add(int(task.parent.id))
            except (TypeError, ValueError):
                continue
        return list(unique_parent_ids)

    def _fetch_parent_titles(self, parent_ids: List[int]) -> Dict[str, str]:
        azure_client = self.connection.clients.get_work_item_tracking_client()
        titles_by_id: Dict[str, str] = {}
        batch_size = 200
        for batch_start in range(0, len(parent_ids), batch_size):
            batch = parent_ids[batch_start:batch_start + batch_size]
            work_items = azure_client.get_work_items(ids=batch, fields=["System.Title"])
            for work_item in work_items:
                if work_item is None:
                    continue
                title = work_item.fields.get("System.Title", "")
                titles_by_id[str(work_item.id)] = title
        return titles_by_id

    def _create_converter_for_criteria(self, criteria: Optional[TaskSearchCriteria],
                                       enrichment: Optional[EnrichmentOptions] = None) -> AzureTaskConverter:
        worktime_extractor = self._create_worktime_extractor_from_criteria(criteria)

        worklog_statuses = self._resolve_transition_statuses(self.config)
        if enrichment and enrichment.worklog_transition_statuses:
            worklog_statuses = enrichment.worklog_transition_statuses

        worklog_extractor = AzureStatusChangeWorklogExtractor(
            transition_statuses=worklog_statuses,
            use_user_name=True,
            worktime_extractor=worktime_extractor
        )

        return AzureTaskConverter(self.config, worklog_extractor, self._story_point_extractor)

    def _create_worktime_extractor_from_criteria(self, criteria: Optional[TaskSearchCriteria]) -> WorkTimeExtractor:
        if self.worktime_extractor_type == WorkTimeExtractorType.BOUNDARY_FROM_LAST_MODIFIED:
            if criteria and criteria.last_modified_date_range:
                start_date, end_date = criteria.last_modified_date_range
                if start_date and end_date:
                    return BoundarySimpleWorkTimeExtractor(start_date, end_date)
        elif self.worktime_extractor_type == WorkTimeExtractorType.BOUNDARY_FROM_RESOLUTION:
            if criteria and criteria.resolution_date_range:
                start_date, end_date = criteria.resolution_date_range
                if start_date and end_date:
                    return BoundarySimpleWorkTimeExtractor(start_date, end_date)

        return SIMPLE_WORKTIME_EXTRACTOR

    @staticmethod
    def _resolve_transition_statuses(config: TasksConfig) -> List[str]:
        all_statuses = []
        for stage_name, statuses in config.workflow.stages.items():
            all_statuses.extend(statuses)
        return all_statuses
