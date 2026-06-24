from typing import Dict, List, Mapping

from ..data.task_data import TaskData
from ..data.task_filter_data import TaskFilterPanel
from ..utils.filter_fields import FieldFilter


class TaskFilterConvertor:

    @staticmethod
    def parse_selections(query_params: Mapping[str, str], field_filters: List[FieldFilter]) -> Dict[str, str]:
        selections = {}
        for field_filter in field_filters:
            value = query_params.get(field_filter.param)
            if value:
                selections[field_filter.param] = value
        return selections

    @staticmethod
    def to_panel(tasks: List[TaskData], selections: Dict[str, str],
                 field_filters: List[FieldFilter]) -> TaskFilterPanel:
        fields = [field_filter.to_field(tasks, selections.get(field_filter.param))
                  for field_filter in field_filters]
        return TaskFilterPanel(
            fields=[field for field in fields if field is not None],
            has_active_selection=bool(selections)
        )
