from typing import List

from django.conf import settings

from tasks.app.api.api_for_task_search import ApiForTaskSearch
from tasks.app.domain.model.task import Task, TaskSearchCriteria, EnrichmentOptions
from velocity.app.spi.task_repository import TaskRepository


class TasksApiRepository(TaskRepository):

    def __init__(self, task_search_api: ApiForTaskSearch):
        self._task_search_api = task_search_api

    async def search(self, search_criteria: TaskSearchCriteria) -> List[Task]:
        enrichment = EnrichmentOptions(
            include_time_tracking=True,
            worklog_transition_statuses=settings.METRICS_IN_PROGRESS_STATUS_CODES
        )
        return await self._task_search_api.search(search_criteria, enrichment)
