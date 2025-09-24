import asyncio
from copy import deepcopy
from typing import List, Optional

from tasks.app.domain.model.config import WorkflowConfig
from tasks.app.domain.model.task import Task, EnrichmentOptions, TaskSearchCriteria, MemberGroup
from ..convertors.member_convertor import MemberConvertor
from ..convertors.task_convertor import TaskConvertor
from ..data.member_data import MemberGroupData
from ..data.task_data import TaskData
from ..utils.federated_data_fetcher import FederatedDataFetcher
from ..utils.federated_data_post_processors import MemberGroupTaskFilter
from ..utils.forecast_population_utils import ForecastPopulationUtils
from ..utils.task_sort_utils import TaskSortUtils


class TasksFacade:

    def __init__(self, task_search_api, forecast_api, task_convertor: TaskConvertor,
                 available_member_groups: List[MemberGroup],
                 current_tasks_search_criteria: TaskSearchCriteria,
                 recently_finished_tasks_search_criteria: TaskSearchCriteria,
                 workflow_config: WorkflowConfig,
                 member_group_task_filter: MemberGroupTaskFilter,
                 member_convertor: MemberConvertor):
        self.task_search_api = task_search_api
        self.forecast_api = forecast_api
        self.available_member_groups = available_member_groups
        self.__current_tasks_search_criteria_template = current_tasks_search_criteria
        self.__recently_finished_tasks_search_criteria_template = recently_finished_tasks_search_criteria
        self.workflow_config = workflow_config
        self.member_group_task_filter = member_group_task_filter
        self.task_convertor = task_convertor
        self.member_convertor = member_convertor

    async def get_tasks(self, member_group_id: Optional[str] = None) -> List[TaskData]:
        tasks = await self._fetch_tasks(member_group_id)
        return [self.task_convertor.convert_task_to_data(task) for task in tasks]

    def get_available_member_groups(self) -> List[MemberGroupData]:
        return [self.member_convertor.convert_member_group_to_data(group) for group in
                self.available_member_groups]

    async def _fetch_tasks(self, member_group_id: Optional[str]) -> List[Task]:
        current_tasks_future = self._build_task_fetcher(self._search_current_tasks, member_group_id)
        recently_finished_tasks_future = self._build_task_fetcher(self._search_recently_finished_tasks, member_group_id)

        current_tasks, recently_finished_tasks = await asyncio.gather(
            current_tasks_future, recently_finished_tasks_future
        )

        all_tasks = current_tasks + recently_finished_tasks

        # Apply batch forecast population to all tasks at once
        await ForecastPopulationUtils.populate_ideal_forecasts_batch(all_tasks, self.forecast_api)

        return all_tasks

    def _build_task_fetcher(self, task_fetcher_func, member_group_id: Optional[str]):
        return (
            FederatedDataFetcher
            .for_(task_fetcher_func)
            .with_result_post_processor(
                lambda all_tasks: self.member_group_task_filter.filter(all_tasks, member_group_id)
            )
            .with_result_post_processor(TaskSortUtils.sort_tasks_by_spent_time)
            .fetch()
        )

    async def _search_current_tasks(self) -> List[Task]:
        search_criteria = self._create_current_tasks_search_criteria()
        enrichment = EnrichmentOptions(include_time_tracking=True, worklog_transition_statuses=self.workflow_config.in_progress_status_codes)
        return await self.task_search_api.search(search_criteria, enrichment)

    async def _search_recently_finished_tasks(self) -> List[Task]:
        search_criteria = self._create_recently_finished_tasks_search_criteria()
        enrichment = EnrichmentOptions(include_time_tracking=True, worklog_transition_statuses=self.workflow_config.in_progress_status_codes)
        return await self.task_search_api.search(search_criteria, enrichment)

    def _create_current_tasks_search_criteria(self):
        return deepcopy(self.__current_tasks_search_criteria_template)

    def _create_recently_finished_tasks_search_criteria(self):
        return deepcopy(self.__recently_finished_tasks_search_criteria_template)
