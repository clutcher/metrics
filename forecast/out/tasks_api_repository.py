from typing import List

from django.conf import settings

from tasks.app.api.api_for_task_hierarchy import ApiForTaskHierarchy
from tasks.app.api.api_for_task_search import ApiForTaskSearch
from tasks.app.domain.model.task import HierarchyTraversalCriteria, EnrichmentOptions
from ..app.spi.task_repository import TaskRepository


class TasksApiRepository(TaskRepository):

    def __init__(self, tasks_search_api: ApiForTaskSearch, tasks_hierarchy_api: ApiForTaskHierarchy):
        self._tasks_search_api = tasks_search_api
        self._tasks_hierarchy_api = tasks_hierarchy_api

    async def get_tasks(self, task_ids: List[str]) -> List:
        enrichment = EnrichmentOptions(
            include_time_tracking=True,
            worklog_transition_statuses=settings.METRICS_IN_PROGRESS_STATUS_CODES
        )
        return await self._tasks_search_api.search_by_ids(task_ids, enrichment)

    async def get_tasks_with_full_hierarchy(self, task_ids: List[str]) -> List:
        criteria = HierarchyTraversalCriteria(
            max_depth=5,
            exclude_done_tasks=True
        )

        return await self._tasks_hierarchy_api.get_tasks_with_full_hierarchy(task_ids, criteria)
