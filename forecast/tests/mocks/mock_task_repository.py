from typing import List
from unittest.mock import AsyncMock

from forecast.app.domain.model.task import Task
from forecast.app.spi.task_repository import TaskRepository


class MockTaskRepository(TaskRepository):
    
    def __init__(self):
        self._mock = AsyncMock()
        
    async def get_tasks(self, task_ids: List[str]) -> List[Task]:
        return await self._mock.get_tasks(task_ids)
    
    async def get_tasks_with_full_hierarchy(self, task_ids: List[str]) -> List[Task]:
        return await self._mock.get_tasks_with_full_hierarchy(task_ids)
    
    @property
    def mock(self) -> AsyncMock:
        return self._mock