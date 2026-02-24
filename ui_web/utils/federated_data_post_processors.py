from typing import Optional, List, Any

from tasks.app.domain.model.task import Task
from tasks.out.convertors.task_conversion_utils import TaskConversionUtils


class MemberGroupTaskFilter:

    def __init__(self, member_group_config: Any) -> None:
        self.member_group_config = member_group_config

    def filter(self, tasks: List[Task], member_group_id: Optional[str]) -> List[Task]:
        if not member_group_id:
            return tasks

        if self._has_custom_filter(member_group_id):
            return tasks

        tasks_assigned_to_member_group = []
        for task in tasks:
            assignee_id = self._get_assignee_id(task)
            if member_group_id == TaskConversionUtils.UNASSIGNED_MEMBER_GROUP_NAME:
                if self._is_assignee_of_unassigned_member_group(assignee_id):
                    tasks_assigned_to_member_group.append(task)
            elif self._is_assignee_of_group(assignee_id, member_group_id):
                tasks_assigned_to_member_group.append(task)

        return tasks_assigned_to_member_group

    def _has_custom_filter(self, member_group_id: str) -> bool:
        if not self.member_group_config or not self.member_group_config.custom_filters:
            return False
        return member_group_id in self.member_group_config.custom_filters

    def _is_assignee_of_unassigned_member_group(self, assignee_id: Optional[str]) -> bool:
        if not assignee_id:
            return True
        assignee_groups = self._get_assignee_member_groups(assignee_id)
        return not assignee_groups or assignee_groups == [None]

    def _is_assignee_of_group(self, assignee_id: Optional[str], member_group_id: str) -> bool:
        return assignee_id and member_group_id in self._get_assignee_member_groups(assignee_id)

    def _get_assignee_member_groups(self, assignee_id: str) -> List[str]:
        assignee_data = self.member_group_config.members.get(assignee_id, {}) if self.member_group_config else {}
        assignee_member_groups = assignee_data.get('member_groups', [])

        if assignee_member_groups:
            return assignee_member_groups

        if self.member_group_config and self.member_group_config.default_member_group_when_missing:
            return [self.member_group_config.default_member_group_when_missing]

        return []

    @staticmethod
    def _get_assignee_id(task: Task) -> Optional[str]:
        if not task.assignment or not task.assignment.assignee:
            return None
        return task.assignment.assignee.id
