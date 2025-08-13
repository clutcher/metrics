from typing import List, Set, Optional

from django.conf import settings

from .member_utils import MemberUtils


class TasksUtils:

    @staticmethod
    def filter_in_progress_tasks(all_tasks: List) -> List:
        current_tasks = []
        for task in all_tasks:
            if (task.system_metadata and
                    task.system_metadata.original_status in settings.METRICS_IN_PROGRESS_STATUS_CODES):
                current_tasks.append(task)
        return current_tasks

    @staticmethod
    def get_task_assignee_ids(tasks: List) -> Set[str]:
        assignees = set()
        for task in tasks:
            if task.assignment and task.assignment.assignee:
                if task.system_metadata and task.system_metadata.original_status in settings.METRICS_IN_PROGRESS_STATUS_CODES:
                    assignees.add(task.assignment.assignee.id)
        return assignees


    @staticmethod
    def get_members_not_assigned_to_tasks(current_tasks: List, member_group_filter: Optional[str] = None) -> List[str]:
        task_assignees = TasksUtils.get_task_assignee_ids(current_tasks)
        members_of_member_grou = MemberUtils.get_all_members_of_member_group(member_group_filter)
        return list(members_of_member_grou.keys() - task_assignees)