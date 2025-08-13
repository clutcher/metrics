from typing import List, Optional, Callable

from .assignee_search_service import AssigneeSearchService
from .convertors.task_metadata_convertor import TaskMetadataPopulator
from .model.config import TasksConfig
from .model.task import TaskSearchCriteria, Task, EnrichmentOptions, WorkTimeExtractorType
from ..api.api_for_task_search import ApiForTaskSearch
from ..spi.task_repository import TaskRepository


class TaskSearchService(ApiForTaskSearch):

    def __init__(self, repository: TaskRepository, task_config: TasksConfig,
                 assignee_search_service: AssigneeSearchService,
                 repository_factory: Callable[[Optional[WorkTimeExtractorType]], TaskRepository],
                 metadata_convertor: TaskMetadataPopulator):
        self._repository = repository
        self._config = task_config
        self._assignee_search_api = assignee_search_service
        self._repository_factory = repository_factory
        self._metadata_convertor = metadata_convertor

    async def search(self, criteria: Optional[TaskSearchCriteria] = None,
                     enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        worktime_extractor_type = self._determine_worktime_extractor_type(enrichment)
        repository = self._repository_factory(worktime_extractor_type)
        tasks = await repository.find_all(search_criteria=criteria, enrichment=enrichment)
        tasks = self._metadata_convertor.populate_metadata_for_tasks(tasks)

        self._assignee_search_api.populate_assignee_cache_from_tasks(tasks)

        return tasks

    async def search_by_ids(self, task_ids: List[str], enrichment: Optional[EnrichmentOptions] = None) -> List[Task]:
        worktime_extractor_type = self._determine_worktime_extractor_type(enrichment)
        repository = self._repository_factory(worktime_extractor_type)
        tasks = await repository.find_all(
            search_criteria=(TaskSearchCriteria(id_filter=task_ids)),
            enrichment=enrichment
        )
        tasks = self._metadata_convertor.populate_metadata_for_tasks(tasks)

        self._assignee_search_api.populate_assignee_cache_from_tasks(tasks)

        return tasks

    @staticmethod
    def _determine_worktime_extractor_type(enrichment: Optional[EnrichmentOptions]) -> Optional[WorkTimeExtractorType]:
        if enrichment and enrichment.worktime_extractor_type:
            return enrichment.worktime_extractor_type
        return None
