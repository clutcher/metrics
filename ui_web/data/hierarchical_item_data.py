from dataclasses import dataclass
from typing import List, Union

from .task_data import TaskData


@dataclass(slots=True)
class HierarchicalItemData:
    name: str
    type: str
    count: int
    items: List[Union['HierarchicalItemData', TaskData]]