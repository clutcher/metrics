from typing import List, Optional
from unittest.mock import AsyncMock

from forecast.app.api.api_for_forecast import ApiForForecast
from forecast.app.domain.model.forecast import ForecastGenerationParameters
from tasks.app.domain.model.task import Task


class MockForecastApi(ApiForForecast):
    
    def __init__(self):
        self._mock = AsyncMock()
        
    async def generate_forecasts_for_tasks(self, tasks: List[Task], 
                                          parameters: ForecastGenerationParameters) -> List[Task]:
        return await self._mock.generate_forecasts_for_tasks(tasks, parameters)
    
    async def generate_forecasts_for_task_ids(self, task_ids: List[str], 
                                             parameters: ForecastGenerationParameters) -> List[Task]:
        return await self._mock.generate_forecasts_for_task_ids(task_ids, parameters)
    
    async def populate_estimations(self, tasks: List[Task], 
                                  parameters: Optional[ForecastGenerationParameters] = None) -> List[Task]:
        return await self._mock.populate_estimations(tasks, parameters)
    
    @property
    def mock(self) -> AsyncMock:
        return self._mock