from abc import ABC, abstractmethod
from typing import List

from ..domain.model.task import Task, HierarchyTraversalCriteria


class ApiForTaskHierarchy(ABC):

    @abstractmethod
    async def get_tasks_with_full_hierarchy(self, task_ids: List[str], criteria: HierarchyTraversalCriteria) -> List[Task]:
        pass