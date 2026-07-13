import logging
from typing import Optional, Dict

from sd_metrics_lib.sources.azure.tasks import AzureTaskProvider
from sd_metrics_lib.utils.time import Duration

from tasks.app.domain.model.config import TasksConfig
from tasks.app.domain.model.task import Task, Assignee, Assignment, TimeTracking, SystemMetadata, MemberGroup, Release
from tasks.out.convertors.task_conversion_utils import TaskConversionUtils

logger = logging.getLogger(__name__)


class AzureTaskConverter:

    def __init__(self, config: TasksConfig, worklog_extractor, story_point_extractor,
                 include_time_tracking: bool = True):
        self.config = config
        self.worklog_extractor = worklog_extractor
        self.story_point_extractor = story_point_extractor
        self.include_time_tracking = include_time_tracking

    def convert_to_task(self, azure_task) -> Task:
        task = self._create_basic_task(azure_task)
        self._populate_assignment(task, azure_task)
        if self.include_time_tracking:
            self._populate_time_tracking(task, azure_task)
        self._populate_system_metadata(task, azure_task)
        self._populate_parent(task, azure_task)
        self._populate_release(task, azure_task)
        self._populate_iteration(task, azure_task)
        self._populate_custom_sort_fields(task, azure_task)
        self._populate_child_tasks(task, azure_task)
        return task

    def _create_basic_task(self, azure_task) -> Task:
        azure_status = azure_task.fields.get("System.State", "")
        story_points = self.story_point_extractor.get_story_points(azure_task)
        child_tasks_count = self._extract_child_tasks_count(azure_task)
        priority_data = azure_task.fields.get("Microsoft.VSTS.Common.Priority")
        priority = int(priority_data) if priority_data else None

        return Task(
            id=str(azure_task.id),
            title=azure_task.fields.get("System.Title", ""),
            status=TaskConversionUtils.normalize_status(azure_status, self.config),
            stage=TaskConversionUtils.get_stage_name_for_status(azure_status, self.config),
            story_points=story_points,
            priority=priority,
            child_tasks_count=child_tasks_count,
            system_metadata=SystemMetadata(original_status="", project_key="", url=""),
            assignment=Assignment(assignee=None, member_group=None),
            time_tracking=TimeTracking(total_spent_time=Duration.zero(), spent_time_by_assignee={}, current_assignee_spent_time=None)
        )

    def _populate_assignment(self, task: Task, azure_task) -> None:
        assignee = self._extract_assignee_from_azure_fields(azure_task)
        member_group_name = TaskConversionUtils.determine_member_group_name(assignee, self.config)
        member_group_id = TaskConversionUtils.create_member_group_id(member_group_name)
        member_group = MemberGroup(id=member_group_id, name=member_group_name)

        task.assignment = Assignment(assignee=assignee, member_group=member_group)

    def _populate_time_tracking(self, task: Task, azure_task) -> None:
        spent_time_by_assignee = self._extract_raw_spent_time_by_assignee(azure_task)
        total_spent_time = TaskConversionUtils.calculate_total_spent_time(spent_time_by_assignee)
        current_assignee_spent_time = TaskConversionUtils.extract_current_assignee_spent_time(
            task.assignment.assignee,
            spent_time_by_assignee
        )

        task.time_tracking = TimeTracking(
            total_spent_time=total_spent_time,
            spent_time_by_assignee=spent_time_by_assignee,
            current_assignee_spent_time=current_assignee_spent_time
        )

    def _populate_system_metadata(self, task: Task, azure_task) -> None:
        azure_status = azure_task.fields.get("System.State", "")
        project_name = azure_task.fields.get("System.TeamProject") or ""

        task.system_metadata = SystemMetadata(
            original_status=azure_status,
            project_key=project_name,
            url=self._build_work_item_url(azure_task.id, project_name)
        )

    def _build_work_item_url(self, work_item_id, project_name: str) -> str:
        return f"{self.config.azure.azure_organization_url.rstrip('/')}/{project_name}/_workitems/edit/{work_item_id}"

    def _populate_release(self, task: Task, azure_task) -> None:
        field = self.config.azure.release_field
        if not field:
            return
        raw_value = azure_task.fields.get(field)
        if not raw_value:
            return
        values = raw_value if isinstance(raw_value, list) else [raw_value]
        releases = []
        for raw in values:
            if not raw:
                continue
            text = str(raw)
            for segment in self._split_release_segments(text):
                name = segment.split('\\')[-1] if '\\' in segment else segment
                if name:
                    releases.append(Release(id=segment, name=name))
        if releases:
            task.releases = releases

    @staticmethod
    def _split_release_segments(text: str) -> list:
        return [segment.strip() for segment in text.split(',') if segment.strip()]

    def _populate_iteration(self, task: Task, azure_task) -> None:
        field = self.config.azure.iteration_field
        if not field:
            return
        raw_value = azure_task.fields.get(field)
        if not raw_value:
            return
        text = str(raw_value)
        task.iteration = text.split('\\')[-1] if '\\' in text else text

    def _populate_custom_sort_fields(self, task: Task, azure_task) -> None:
        custom_sort_fields = {}
        for field_name in self.config.sorting.custom_sort_field_names():
            raw_value = azure_task.fields.get(field_name)
            if raw_value is not None:
                custom_sort_fields[field_name] = str(raw_value)
        if custom_sort_fields:
            task.custom_sort_fields = custom_sort_fields

    def _populate_parent(self, task: Task, azure_task) -> None:
        parent_id_value = azure_task.fields.get("System.Parent")
        if not parent_id_value:
            return

        project_name = azure_task.fields.get("System.TeamProject") or ""
        parent_id = str(parent_id_value)

        task.parent = Task(
            id=parent_id,
            title='',
            system_metadata=SystemMetadata(
                original_status='',
                project_key=project_name,
                url=self._build_work_item_url(parent_id, project_name)
            ),
            assignment=Assignment(assignee=None, member_group=None),
            time_tracking=TimeTracking()
        )

    @staticmethod
    def _extract_assignee_from_azure_fields(azure_task) -> Optional[Assignee]:
        assigned_to = azure_task.fields.get("System.AssignedTo")
        if not assigned_to:
            return None

        return Assignee(
            id=assigned_to.get("displayName", ""),
            display_name=assigned_to.get("displayName", ""),
            avatar_url=assigned_to.get("imageUrl"),
        )

    def _extract_raw_spent_time_by_assignee(self, azure_task) -> Dict[str, Duration]:
        try:
            return self.worklog_extractor.get_work_time_per_user(azure_task)
        except Exception as e:
            logger.error(f"Error extracting spent time for work item {azure_task.id}: {e}")
            return {}

    def _populate_child_tasks(self, task: Task, azure_task) -> None:
        child_tasks = azure_task.fields.get(AzureTaskProvider.CHILD_TASKS_CUSTOM_FIELD_NAME, [])
        if child_tasks:
            converted_child_tasks = []
            for child_task in child_tasks:
                try:
                    converted_child = self.convert_to_task(child_task)
                    converted_child_tasks.append(converted_child)
                except Exception as e:
                    logger.error(f"Error converting child task {child_task.id}: {e}")

            task.child_tasks = converted_child_tasks if converted_child_tasks else None

    @staticmethod
    def _extract_child_tasks_count(azure_task) -> Optional[int]:
        child_tasks = azure_task.fields.get(AzureTaskProvider.CHILD_TASKS_CUSTOM_FIELD_NAME, [])
        return len(child_tasks) if child_tasks else None
