from typing import List, Union, Optional, Tuple, Any

from tasks.app.domain.model.config import SortingConfig
from tasks.app.domain.model.task import Task
from .task_data_extractor import TaskDataExtractor
from ..data.task_data import TaskData

SORT_EXTRACTORS = {
    'priority': ('numeric', TaskDataExtractor.extract_priority),
    'health': ('numeric', TaskDataExtractor.extract_health_status_value),
    'spent_time': ('numeric', TaskDataExtractor.extract_spent_time_seconds),
    'assignee': ('string', TaskDataExtractor.extract_assignee_name),
}


class TaskSortUtils:

    @staticmethod
    def sort_tasks(
            tasks: List[Union[TaskData, 'Task']],
            sorting_config: Optional[SortingConfig] = None
    ) -> List[Union[TaskData, 'Task']]:
        if not tasks or not sorting_config:
            return tasks
        return sorted(tasks, key=lambda task: TaskSortUtils._get_sort_key(task, sorting_config))

    @staticmethod
    def _get_sort_key(task: Union[TaskData, 'Task'], sorting_config: SortingConfig) -> Tuple[Any, ...]:
        task_stage = getattr(task, 'stage', None)
        criteria_string = sorting_config.stage_sort_overrides.get(task_stage, sorting_config.default_sort_criteria)

        sort_key_parts = []
        for criteria_part in criteria_string.split(','):
            criteria_part = criteria_part.strip()
            if not criteria_part:
                continue
            is_ascending = not criteria_part.startswith('-')
            criterion_name = criteria_part.lstrip('-')
            if criterion_name in SORT_EXTRACTORS:
                value_type, extractor_function = SORT_EXTRACTORS[criterion_name]
                extracted_value = extractor_function(task)
                sort_key_parts.append(TaskSortUtils._apply_sort_direction(extracted_value, value_type, is_ascending))
        return tuple(sort_key_parts)

    @staticmethod
    def _apply_sort_direction(value: Any, value_type: str, is_ascending: bool) -> Any:
        if value_type == 'numeric':
            return value if is_ascending else -value
        if is_ascending:
            return value
        return '~' * 1000 if not value else chr(255) + value
