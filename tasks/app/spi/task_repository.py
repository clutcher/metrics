from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.model.task import TaskSearchCriteria, Task, EnrichmentOptions


class TaskRepository(ABC):

    @abstractmethod
    async def find_all(self,
                       search_criteria: Optional[TaskSearchCriteria] = None,
                       enrichment: Optional[EnrichmentOptions] = None
                       ) -> List[Task]:
        pass
