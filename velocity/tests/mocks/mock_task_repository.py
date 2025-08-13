from typing import List
from unittest.mock import AsyncMock

from tasks.app.domain.model.task import Task, TaskSearchCriteria
from velocity.app.spi.task_repository import TaskRepository


class MockTaskRepository(TaskRepository):
    def __init__(self):
        self._mock = AsyncMock()

    async def search(self, search_criteria: TaskSearchCriteria) -> List[Task]:
        return await self._mock.search(search_criteria)
    
    @property
    def mock(self) -> AsyncMock:
        return self._mock