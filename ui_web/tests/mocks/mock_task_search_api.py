from typing import List, Optional
from unittest.mock import AsyncMock

from tasks.app.api.api_for_task_search import ApiForTaskSearch
from tasks.app.domain.model.task import TaskSearchCriteria, Task, EnrichmentOptions


class MockTaskSearchApi(ApiForTaskSearch):
    
    def __init__(self):
        self._mock = AsyncMock()
        
    async def search(self, criteria: Optional[TaskSearchCriteria] = None, 
                     enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        return await self._mock.search(criteria, enrichment)
    
    async def search_by_ids(self, task_ids: List[str], 
                           enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        return await self._mock.search_by_ids(task_ids, enrichment)
    
    @property
    def mock(self) -> AsyncMock:
        return self._mock