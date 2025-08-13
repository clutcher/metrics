from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.model.task import TaskSearchCriteria, Task, EnrichmentOptions


class ApiForTaskSearch(ABC):

    @abstractmethod
    async def search(self, criteria: Optional[TaskSearchCriteria] = None, enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        pass
    
    @abstractmethod
    async def search_by_ids(self, task_ids: List[str], enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        pass
