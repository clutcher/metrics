from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Tuple

from sd_metrics_lib.utils.enums import HealthStatus

from .natural_sort import NATURAL_KEY
from ..data.task_data import TaskData
from ..data.task_filter_data import (
    FilterField, FilterOption, NO_PARENT_OPTION_ID, UNASSIGNED_OPTION_ID
)

LabelledValue = Optional[Tuple[str, str]]
LabelledValues = List[Tuple[str, str]]


def _sorted_options(labels_by_id: dict) -> List[FilterOption]:
    return [FilterOption(id=value_id, label=label)
            for value_id, label in sorted(labels_by_id.items(), key=lambda pair: NATURAL_KEY(pair[1]))]


class FieldFilter(ABC):

    def __init__(self, param: str, label: str, requires_enrichment: bool = False):
        self.param = param
        self.label = label
        self.requires_enrichment = requires_enrichment

    def to_field(self, tasks: List[TaskData], selected: Optional[str]) -> Optional[FilterField]:
        options = self._build_options(tasks)
        if not options:
            return None
        for option in options:
            option.selected = option.id == selected
        return FilterField(param=self.param, label=self.label, options=options)

    @abstractmethod
    def _build_options(self, tasks: List[TaskData]) -> List[FilterOption]:
        ...

    @abstractmethod
    def matches(self, task: TaskData, selected: str) -> bool:
        ...


class SingleValueFilter(FieldFilter):

    def __init__(self, param: str, label: str, value_of: Callable[[TaskData], LabelledValue],
                 missing_option_id: Optional[str] = None, missing_option_label: Optional[str] = None):
        super().__init__(param, label)
        self._value_of = value_of
        self._missing_option_id = missing_option_id
        self._missing_option_label = missing_option_label

    def _build_options(self, tasks: List[TaskData]) -> List[FilterOption]:
        labels_by_id = {}
        has_missing = False
        for task in tasks:
            value = self._value_of(task)
            if value is None:
                has_missing = True
            else:
                labels_by_id.setdefault(value[0], value[1])
        options = _sorted_options(labels_by_id)
        if has_missing and self._missing_option_id is not None:
            options.insert(0, FilterOption(id=self._missing_option_id, label=self._missing_option_label))
        return options

    def matches(self, task: TaskData, selected: str) -> bool:
        if not selected:
            return True
        if self._missing_option_id is not None and selected == self._missing_option_id:
            return self._value_of(task) is None
        value = self._value_of(task)
        return value is not None and value[0] == selected


class MultiValueFilter(FieldFilter):

    def __init__(self, param: str, label: str, values_of: Callable[[TaskData], LabelledValues]):
        super().__init__(param, label)
        self._values_of = values_of

    def _build_options(self, tasks: List[TaskData]) -> List[FilterOption]:
        labels_by_id = {}
        for task in tasks:
            for value_id, label in self._values_of(task):
                labels_by_id.setdefault(value_id, label)
        return _sorted_options(labels_by_id)

    def matches(self, task: TaskData, selected: str) -> bool:
        if not selected:
            return True
        return any(value_id == selected for value_id, _ in self._values_of(task))


class FixedOptionsFilter(FieldFilter):

    def __init__(self, param: str, label: str, options: LabelledValues,
                 value_of: Callable[[TaskData], Optional[str]], requires_enrichment: bool = False):
        super().__init__(param, label, requires_enrichment)
        self._options = options
        self._value_of = value_of

    def _build_options(self, tasks: List[TaskData]) -> List[FilterOption]:
        return [FilterOption(id=option_id, label=label) for option_id, label in self._options]

    def matches(self, task: TaskData, selected: str) -> bool:
        if not selected:
            return True
        return self._value_of(task) == selected


def _priority_value(task: TaskData) -> LabelledValue:
    if task.priority is None:
        return None
    return str(task.priority), f"Priority {task.priority}"


def _format_points(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


def _story_points_value(task: TaskData) -> LabelledValue:
    if task.story_points is None:
        return None
    text = _format_points(task.story_points)
    return text, text


def _assignee_value(task: TaskData) -> LabelledValue:
    assignee = task.assignment.assignee
    if assignee is None:
        return None
    return assignee.id, assignee.display_name


def _member_group_value(task: TaskData) -> LabelledValue:
    member_group = task.assignment.member_group
    if member_group is None:
        return None
    return member_group.id, member_group.name


def _parent_value(task: TaskData) -> LabelledValue:
    parent = task.parent
    if parent is None:
        return None
    return parent.id, parent.title or parent.id


def _stage_value(task: TaskData) -> LabelledValue:
    if not task.stage:
        return None
    return task.stage, task.stage


def _status_value(task: TaskData) -> LabelledValue:
    status = task.system_metadata.original_status if task.system_metadata else None
    if not status:
        return None
    return status, status


def _release_values(task: TaskData) -> LabelledValues:
    return [(release.id, release.name) for release in task.releases or []]


def _iteration_value(task: TaskData) -> LabelledValue:
    if not task.iteration:
        return None
    return task.iteration, task.iteration


def _health_value(task: TaskData) -> Optional[str]:
    if not task.forecast or not task.forecast.health_status:
        return None
    return task.forecast.health_status.name


def _health_options() -> LabelledValues:
    return [(status.name, status.name.title()) for status in HealthStatus]


_FIELD_FILTERS = {
    'priority': SingleValueFilter('priority', 'Priorities', _priority_value),
    'story_points': SingleValueFilter('story_points', 'Story points', _story_points_value),
    'assignee': SingleValueFilter('assignee', 'Assignees', _assignee_value, UNASSIGNED_OPTION_ID, 'Unassigned'),
    'member_group': SingleValueFilter('member_group', 'Member groups', _member_group_value),
    'parent': SingleValueFilter('parent', 'Parent tickets', _parent_value, NO_PARENT_OPTION_ID, 'No parent'),
    'stage': SingleValueFilter('stage', 'Stages', _stage_value),
    'status': SingleValueFilter('status', 'Statuses', _status_value),
    'release': MultiValueFilter('release', 'Releases', _release_values),
    'iteration': SingleValueFilter('iteration', 'Iterations', _iteration_value),
    'health': FixedOptionsFilter('health', 'Health', _health_options(), _health_value, requires_enrichment=True),
}


def build_field_filters(field_names: List[str]) -> List[FieldFilter]:
    return [_FIELD_FILTERS[name] for name in field_names if name in _FIELD_FILTERS]
