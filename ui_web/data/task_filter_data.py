from dataclasses import dataclass, field
from typing import List

UNASSIGNED_OPTION_ID = "__unassigned__"
NO_PARENT_OPTION_ID = "__no_parent__"


@dataclass(slots=True)
class FilterOption:
    id: str
    label: str
    selected: bool = False


@dataclass(slots=True)
class FilterField:
    param: str
    label: str
    options: List[FilterOption]


@dataclass(slots=True)
class TaskFilterPanel:
    fields: List[FilterField] = field(default_factory=list)
    has_active_selection: bool = False
