from abc import ABC, abstractmethod
from typing import List

from ..domain.model.forecast import ForecastGenerationParameters
from ..domain.model.task import Task


class ApiForForecast(ABC):

    @abstractmethod
    async def generate_forecasts_for_tasks(
        self,
        tasks: List[Task],
        parameters: ForecastGenerationParameters
    ) -> List[Task]:
        pass

    @abstractmethod
    async def generate_forecasts_for_task_ids(
        self,
        task_ids: List[str],
        parameters: ForecastGenerationParameters
    ) -> List[Task]:
        pass
