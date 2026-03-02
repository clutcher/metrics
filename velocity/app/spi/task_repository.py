from abc import ABC, abstractmethod
from typing import List, Optional

from tasks.app.domain.model.task import Task, TaskSearchCriteria, EnrichmentOptions


class TaskRepository(ABC):

    @abstractmethod
    async def search(self, search_criteria: TaskSearchCriteria,
                     enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        pass
