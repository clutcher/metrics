from typing import Callable, List, Set, Union, Optional, Tuple, Any

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


class TaskSortUtils:

    @staticmethod
    def sort_tasks(
            tasks: List[Union[TaskData, 'Task']],
            sorting_config: Optional[SortingConfig] = None
    ) -> List[Union[TaskData, 'Task']]:
        return TaskSortUtils._sort(tasks, lambda task: task, sorting_config)

    @staticmethod
    def sort_by_linked_task(
            items: List[Any],
            task_accessor: Callable[[Any], Union[TaskData, 'Task']],
            sorting_config: Optional[SortingConfig] = None
    ) -> List[Any]:
        return TaskSortUtils._sort(items, task_accessor, sorting_config)

    @staticmethod
    def _sort(
            items: List[Any],
            task_accessor: Callable[[Any], Union[TaskData, 'Task']],
            sorting_config: Optional[SortingConfig]
    ) -> List[Any]:
        if not items or not sorting_config:
            return items
        custom_field_names = set(sorting_config.custom_sort_field_names())
        criteria_string = TaskSortUtils._resolve_criteria_string(items, task_accessor, sorting_config)
        criteria = TaskSortUtils._parse_criteria(criteria_string, custom_field_names)

        sorted_items = list(items)
        for extractor, is_ascending in reversed(criteria):
            sorted_items.sort(key=lambda item: extractor(task_accessor(item)), reverse=not is_ascending)
        return sorted_items

    @staticmethod
    def _resolve_criteria_string(
            items: List[Any],
            task_accessor: Callable[[Any], Union[TaskData, 'Task']],
            sorting_config: SortingConfig
    ) -> str:
        stages = {getattr(task_accessor(item), 'stage', None) for item in items}
        if len(stages) == 1:
            single_stage = next(iter(stages))
            return sorting_config.stage_sort_overrides.get(single_stage, sorting_config.default_sort_criteria)
        return sorting_config.default_sort_criteria

    @staticmethod
    def _parse_criteria(
            criteria_string: str,
            custom_field_names: Set[str]
    ) -> List[Tuple[Callable[[Union[TaskData, 'Task']], Any], bool]]:
        criteria = []
        for criteria_part in criteria_string.split(','):
            criteria_part = criteria_part.strip()
            if not criteria_part:
                continue
            is_ascending = not criteria_part.startswith('-')
            criterion_name = criteria_part.lstrip('-')
            extractor = TaskSortUtils._build_extractor(criterion_name, custom_field_names)
            if extractor is not None:
                criteria.append((extractor, is_ascending))
        return criteria

    @staticmethod
    def _build_extractor(
            criterion_name: str,
            custom_field_names: Set[str]
    ) -> Optional[Callable[[Union[TaskData, 'Task']], Any]]:
        if criterion_name in SORT_EXTRACTORS:
            value_type, extractor_function = SORT_EXTRACTORS[criterion_name]
            if value_type == 'numeric':
                return extractor_function
            return lambda task: _NATURAL_KEY(str(extractor_function(task) or ""))
        if criterion_name in custom_field_names:
            return lambda task: TaskSortUtils._natural_missing_key(
                TaskSortUtils._read_custom_sort_field(task, criterion_name)
            )
        return None

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
