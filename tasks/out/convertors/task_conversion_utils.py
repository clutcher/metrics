from datetime import datetime
from typing import Optional, Dict

from dateutil import parser
from sd_metrics_lib.utils.time import Duration

from tasks.app.domain.model.config import TasksConfig
from tasks.app.domain.model.task import Assignee, TaskStatus


class TaskConversionUtils:

    UNASSIGNED_MEMBER_GROUP_ID = 'unassigned'

    @staticmethod
    def normalize_status(status: str, config: TasksConfig) -> Optional[TaskStatus]:
        if status in config.workflow.in_progress_status_codes:
            return TaskStatus.IN_PROGRESS
        elif status in config.workflow.done_status_codes:
            return TaskStatus.DONE
        else:
            return TaskStatus.TODO

    @staticmethod
    def parse_date(date_str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return parser.parse(date_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def determine_member_group(assignee: Optional[Assignee], config: TasksConfig) -> str:
        if assignee and assignee.id:
            assignee_member_groups = config.get_assignee_member_groups(assignee.id)
            return assignee_member_groups[0] if assignee_member_groups else TaskConversionUtils.UNASSIGNED_MEMBER_GROUP_ID
        return TaskConversionUtils.UNASSIGNED_MEMBER_GROUP_ID

    @staticmethod
    def create_member_group_id(team_name: str) -> str:
        return team_name.lower().replace(' ', '-')

    @staticmethod
    def calculate_total_spent_time(spent_time_by_assignee: Dict[str, Duration]) -> Duration:
        return Duration.sum(spent_time_by_assignee.values()) if spent_time_by_assignee else Duration.zero()

    @staticmethod
    def extract_current_assignee_spent_time(assignee: Optional[Assignee], spent_time_by_assignee: Dict[str, Duration]) -> Optional[Duration]:
        if not assignee or not spent_time_by_assignee:
            return None

        current_assignee_spent_time = spent_time_by_assignee.get(assignee.id)
        if current_assignee_spent_time is not None:
            return current_assignee_spent_time

        for assignee_id, time_spent in spent_time_by_assignee.items():
            if assignee_id == assignee.display_name:
                return time_spent

        return None

    @staticmethod
    def get_stage_statuses_for_status(status: str, config: TasksConfig) -> Optional[list]:
        for stage_name, statuses in config.workflow.stages.items():
            if status in statuses:
                return statuses
        return None

    @staticmethod
    def get_stage_name_for_status(status: str, config: TasksConfig) -> Optional[str]:
        for stage_name, statuses in config.workflow.stages.items():
            if status in statuses:
                return stage_name
        return None
