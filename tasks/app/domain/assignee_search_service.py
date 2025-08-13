from typing import Optional, Dict, List

from .model.task import Assignee, Task
from ..api.api_for_assignee_search import ApiForAssigneeSearch


class AssigneeSearchService(ApiForAssigneeSearch):

    def __init__(self):
        self._assignee_cache: Dict[str, Assignee] = {}

    def get_assignee_by_id(self, assignee_id: str) -> Optional[Assignee]:
        return self._assignee_cache.get(assignee_id)

    def populate_assignee_cache_from_tasks(self, tasks: List[Task]) -> None:
        visited_task_ids = set()
        for task in tasks:
            self._populate_from_single_task(task, visited_task_ids)

    def _populate_from_single_task(self, task: Task, visited_task_ids: set) -> None:
        if task.id in visited_task_ids:
            return
        visited_task_ids.add(task.id)

        if task.assignment and task.assignment.assignee:
            assignee = task.assignment.assignee
            self._assignee_cache[assignee.id] = assignee

        if task.time_tracking and task.time_tracking.spent_time_by_assignee:
            for assignee_id in task.time_tracking.spent_time_by_assignee.keys():
                if assignee_id not in self._assignee_cache:
                    assignee = Assignee(id=assignee_id, display_name=assignee_id)
                    self._assignee_cache[assignee_id] = assignee

        if task.child_tasks:
            for child_task in task.child_tasks:
                self._populate_from_single_task(child_task, visited_task_ids)