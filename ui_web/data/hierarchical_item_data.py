from dataclasses import dataclass
from typing import List, Optional, Union

from .task_data import TaskData


@dataclass(slots=True)
class HierarchicalItemData:
    name: str
    type: str
    count: int
    items: List[Union['HierarchicalItemData', TaskData]]
    summary: Optional[object] = None