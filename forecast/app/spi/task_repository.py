from abc import ABC, abstractmethod
from typing import List

from ..domain.model.task import Task


class TaskRepository(ABC):

    @abstractmethod
    async def get_tasks(self, task_ids: List[str]) -> List[Task]:
        pass

    @abstractmethod
    async def get_tasks_with_full_hierarchy(self, task_ids: List[str]) -> List[Task]:
        pass