import logging
from typing import Optional, Dict

from sd_metrics_lib.utils.time import Duration

from tasks.app.domain.model.config import TasksConfig
from tasks.app.domain.model.task import Task, Assignee, Assignment, TimeTracking, SystemMetadata, MemberGroup
from tasks.out.convertors.task_conversion_utils import TaskConversionUtils

logger = logging.getLogger(__name__)


class JiraTaskConverter:

    def __init__(self, config: TasksConfig, worklog_extractor, story_point_extractor):
        self.config = config
        self.worklog_extractor = worklog_extractor
        self.story_point_extractor = story_point_extractor

    def convert_to_task(self, jira_task: dict) -> Task:
        task = self._create_basic_task(jira_task)
        self._populate_assignment(task, jira_task)
        self._populate_time_tracking(task, jira_task)
        self._populate_system_metadata(task, jira_task)
        self._populate_child_tasks(task, jira_task)
        return task

    def _create_basic_task(self, jira_task: dict) -> Task:
        task_fields = jira_task['fields']
        jira_status = task_fields.get('status', {}).get('name', '')
        story_points = self.story_point_extractor.get_story_points(jira_task)
        child_tasks_count = self._extract_child_tasks_count(jira_task)
        priority_data = task_fields.get('priority')
        priority = int(priority_data.get('id')) if priority_data and priority_data.get('id') else None

        return Task(
            id=jira_task['key'],
            title=task_fields.get('summary', ''),
            created_at=TaskConversionUtils.parse_date(task_fields.get('created')),
            updated_at=TaskConversionUtils.parse_date(task_fields.get('updated')),
            status=TaskConversionUtils.normalize_status(jira_status, self.config),
            stage=TaskConversionUtils.get_stage_name_for_status(jira_status, self.config),
            story_points=story_points,
            priority=priority,
            child_tasks_count=child_tasks_count,
            system_metadata=SystemMetadata(original_status="", project_key="", url=""),
            assignment=Assignment(assignee=None, member_group=None),
            time_tracking=TimeTracking(total_spent_time=None, spent_time_by_assignee={}, current_assignee_spent_time=None)
        )

    def _populate_assignment(self, task: Task, jira_task: dict) -> None:
        assignee = self._extract_assignee_from_jira_fields(jira_task)
        member_group_name = TaskConversionUtils.determine_member_group(assignee, self.config)
        member_group_id = TaskConversionUtils.create_member_group_id(member_group_name)
        member_group = MemberGroup(id=member_group_id, name=member_group_name)

        task.assignment = Assignment(assignee=assignee, member_group=member_group)

    def _populate_time_tracking(self, task: Task, jira_task: dict) -> None:
        spent_time_by_assignee = self._extract_raw_spent_time_by_assignee(jira_task)
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

    def _populate_system_metadata(self, task: Task, jira_task: dict) -> None:
        task_fields = jira_task['fields']
        jira_status = task_fields.get('status', {}).get('name', '')
        project_key = jira_task['key'].split('-')[0]
        url = f"{self.config.jira.jira_server_url.rstrip('/')}/browse/{jira_task['key']}"

        task.system_metadata = SystemMetadata(
            original_status=jira_status,
            project_key=project_key,
            url=url
        )

    @staticmethod
    def _extract_assignee_from_jira_fields(jira_task: dict) -> Optional[Assignee]:
        task_fields = jira_task['fields']
        if not task_fields.get('assignee'):
            return None

        assignee_data = task_fields['assignee']
        return Assignee(
            id=assignee_data.get('displayName', ''),
            display_name=assignee_data.get('displayName', ''),
            avatar_url=assignee_data.get('avatarUrls', {}).get('32x32')
        )

    def _extract_raw_spent_time_by_assignee(self, jira_task: dict) -> Dict[str, Duration]:
        try:
            return self.worklog_extractor.get_work_time_per_user(jira_task)
        except Exception as e:
            logger.error(f"Error extracting spent time for {jira_task.get('key', 'unknown')}: {e}")
            return {}

    def _populate_child_tasks(self, task: Task, jira_task) -> None:
        child_tasks = jira_task.get('fields', {}).get('subtasks')
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
    def _extract_child_tasks_count(jira_task: dict) -> Optional[int]:
        child_tasks = jira_task.get('fields', {}).get('subtasks')
        if child_tasks is not None:
            return len(child_tasks)
        return None
