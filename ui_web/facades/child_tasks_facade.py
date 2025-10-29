from typing import List, Optional

from tasks.app.domain.model.task import Task, TaskSearchCriteria, EnrichmentOptions
from ..convertors.task_convertor import TaskConvertor
from ..data.task_data import TaskData
from ..utils.federated_data_fetcher import FederatedDataFetcher
from ..utils.forecast_population_utils import ForecastPopulationUtils


class ChildTasksFacade:

    def __init__(self, task_search_api, forecast_api, task_convertor: TaskConvertor):
        self.task_search_api = task_search_api
        self.forecast_api = forecast_api
        self.task_convertor = task_convertor

    async def get_child_tasks(self, parent_task_id: str) -> List[TaskData]:
        enriched_child_tasks = await self._fetch_child_tasks(parent_task_id)
        return [self.task_convertor.convert_task_to_data(task) for task in enriched_child_tasks]

    async def _fetch_child_tasks(self, parent_task_id: str) -> List[Task]:
        return await (
            self._build_child_task_fetcher(parent_task_id)
            .fetch()
        )

    def _build_child_task_fetcher(self, parent_task_id: str) -> FederatedDataFetcher:
        return (
            FederatedDataFetcher
            .for_(lambda: self._search_child_tasks(parent_task_id))
            .with_foreach_populator(lambda task: ForecastPopulationUtils.populate_ideal_forecast_for_task(task, self.forecast_api))
        )

    async def _search_child_tasks(self, parent_task_id: str) -> List[Task]:
        search_criteria = TaskSearchCriteria(id_filter=[parent_task_id])
        enrichment = EnrichmentOptions(include_time_tracking=True)
        parent_tasks = await self.task_search_api.search(search_criteria, enrichment)
        return self._extract_child_tasks_from_parent(parent_tasks[0] if parent_tasks else None)

    @staticmethod
    def _extract_child_tasks_from_parent(parent_task: Optional[Task]) -> List[Task]:
        if not parent_task or not parent_task.child_tasks:
            return []
        else:
            return parent_task.child_tasks


