from typing import Dict, List, Mapping

from ..convertors.task_filter_convertor import TaskFilterConvertor
from ..data.task_data import TaskData
from ..data.task_filter_data import TaskFilterPanel
from ..utils.filter_fields import FieldFilter
from ..utils.task_filter_utils import TaskFilterUtils


class TaskFilterFacade:

    def __init__(self, field_filters: List[FieldFilter]):
        self._field_filters = field_filters

    def parse_selections(self, query_params: Mapping[str, str]) -> Dict[str, str]:
        return TaskFilterConvertor.parse_selections(query_params, self._field_filters)

    def get_panel(self, tasks: List[TaskData], selections: Dict[str, str]) -> TaskFilterPanel:
        return TaskFilterConvertor.to_panel(tasks, selections, self._field_filters)

    def filter_tasks(self, tasks: List[TaskData], selections: Dict[str, str]) -> List[TaskData]:
        return TaskFilterUtils.filter_tasks(tasks, selections, self._field_filters)

    def requires_full_fetch(self, selections: Dict[str, str]) -> bool:
        return any(field_filter.requires_enrichment for field_filter in self._field_filters
                   if field_filter.param in selections)
