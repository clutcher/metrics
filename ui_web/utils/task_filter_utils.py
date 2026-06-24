from typing import Dict, List

from ..data.task_data import TaskData
from .filter_fields import FieldFilter


class TaskFilterUtils:

    @staticmethod
    def filter_tasks(tasks: List[TaskData], selections: Dict[str, str],
                     field_filters: List[FieldFilter]) -> List[TaskData]:
        active_filters = [field_filter for field_filter in field_filters
                          if field_filter.param in selections]
        if not active_filters:
            return tasks
        return [task for task in tasks if TaskFilterUtils._matches_all(task, selections, active_filters)]

    @staticmethod
    def _matches_all(task: TaskData, selections: Dict[str, str],
                     active_filters: List[FieldFilter]) -> bool:
        return all(field_filter.matches(task, selections[field_filter.param])
                   for field_filter in active_filters)
