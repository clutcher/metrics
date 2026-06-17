import functools
from typing import List, Set, Union, Optional, Tuple, Any

from natsort import natsort_keygen, ns

from tasks.app.domain.model.config import SortingConfig
from tasks.app.domain.model.task import Task
from .task_data_extractor import TaskDataExtractor
from ..data.task_data import TaskData

SORT_EXTRACTORS = {
    'priority': ('numeric', TaskDataExtractor.extract_priority),
    'health': ('numeric', TaskDataExtractor.extract_health_status_value),
    'spent_time': ('numeric', TaskDataExtractor.extract_spent_time_seconds),
    'assignee': ('natural', TaskDataExtractor.extract_assignee_name),
}

_NATURAL_KEY = natsort_keygen(alg=ns.IGNORECASE)


@functools.total_ordering
class _DescendingKey:
    __slots__ = ('value',)

    def __init__(self, value: Any):
        self.value = value

    def __eq__(self, other: '_DescendingKey') -> bool:
        return self.value == other.value

    def __lt__(self, other: '_DescendingKey') -> bool:
        return other.value < self.value


class TaskSortUtils:

    @staticmethod
    def sort_tasks(
            tasks: List[Union[TaskData, 'Task']],
            sorting_config: Optional[SortingConfig] = None
    ) -> List[Union[TaskData, 'Task']]:
        if not tasks or not sorting_config:
            return tasks
        custom_field_names = set(sorting_config.custom_sort_field_names())
        return sorted(tasks, key=lambda task: TaskSortUtils._get_sort_key(task, sorting_config, custom_field_names))

    @staticmethod
    def build_sort_key(
            task: Union[TaskData, 'Task'],
            sorting_config: SortingConfig
    ) -> Tuple[Any, ...]:
        custom_field_names = set(sorting_config.custom_sort_field_names())
        return TaskSortUtils._get_sort_key(task, sorting_config, custom_field_names)

    @staticmethod
    def _get_sort_key(
            task: Union[TaskData, 'Task'],
            sorting_config: SortingConfig,
            custom_field_names: Set[str]
    ) -> Tuple[Any, ...]:
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
                key_part = extracted_value if value_type == 'numeric' else _NATURAL_KEY(str(extracted_value or ""))
            elif criterion_name in custom_field_names:
                key_part = TaskSortUtils._natural_missing_key(TaskSortUtils._read_custom_sort_field(task, criterion_name))
            else:
                continue
            sort_key_parts.append(key_part if is_ascending else _DescendingKey(key_part))
        return tuple(sort_key_parts)

    @staticmethod
    def _natural_missing_key(value: Optional[str]) -> Tuple[Any, ...]:
        if not value:
            return (1,)
        return (0, _NATURAL_KEY(str(value)))

    @staticmethod
    def _read_custom_sort_field(task: Union[TaskData, 'Task'], field_name: str) -> Optional[str]:
        custom_sort_fields = getattr(task, 'custom_sort_fields', None)
        if not custom_sort_fields:
            return None
        return custom_sort_fields.get(field_name)
