from typing import List, Optional
from unittest.mock import AsyncMock

from tasks.app.domain.model.task import Task, TaskSearchCriteria, EnrichmentOptions
from velocity.app.spi.task_repository import TaskRepository


class MockTaskRepository(TaskRepository):
    def __init__(self):
        self._mock = AsyncMock()

    async def search(self, search_criteria: TaskSearchCriteria,
                     enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        return await self._mock.search(search_criteria, enrichment)
    
    @property
    def mock(self) -> AsyncMock:
        return self._mock