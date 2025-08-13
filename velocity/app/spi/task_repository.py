from abc import ABC, abstractmethod
from typing import List

from tasks.app.domain.model.task import Task, TaskSearchCriteria


class TaskRepository(ABC):

    @abstractmethod
    async def search(self, search_criteria: TaskSearchCriteria) -> List[Task]:
        pass
