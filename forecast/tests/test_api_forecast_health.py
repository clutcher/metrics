import unittest
from unittest.mock import AsyncMock

from sd_metrics_lib.utils.time import TimePolicy

from forecast.app.domain.forecast_service import ForecastService
from forecast.app.domain.model.config import ForecastConfig, CalculationConfig, SeniorityConfig
from forecast.tests.fixtures.forecast_builders import ForecastParametersBuilder, BusinessVelocityScenarios
from forecast.tests.fixtures.task_builders import BusinessScenarios
from forecast.tests.mocks.mock_task_repository import MockTaskRepository
from forecast.tests.mocks.mock_velocity_repository import MockVelocityRepository


class TestApiForecastHealth(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.task_repository = MockTaskRepository()
        self.velocity_repository = MockVelocityRepository()
        self.config = self._create_test_config()
        self.ideal_time_policy = TimePolicy.BUSINESS_HOURS
        
        self.forecast_service = ForecastService(
            self.task_repository,
            self.velocity_repository,
            self.config,
            self.ideal_time_policy
        )
    
    def _create_test_config(self) -> ForecastConfig:
        return ForecastConfig(
            seniority=SeniorityConfig(
                seniority_levels={"senior": 2.0, "junior": 1.0},
                default_seniority_level_when_missing="junior"
            ),
            calculation=CalculationConfig(
                ideal_hours_per_day=8.0,
                story_points_to_ideal_hours_convertion_ratio=4.0,
                default_story_points_value_when_missing=1.0,
                default_health_status_when_missing="GREEN"
            )
        )
    
    async def test_shouldGenerateForecastWithHealthStatusWhenTaskHasTimeTracking(self):
        task = BusinessScenarios.green_health_task()
        tasks = [task]
        parameters = ForecastParametersBuilder.default_parameters().build()
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        self.assertIsNotNone(result[0].forecast)
        self.assertIsNotNone(result[0].forecast.target.health_status)
    
    async def test_shouldGenerateForecastWithHealthStatusWhenTaskHasNoTimeTracking(self):
        task = BusinessScenarios.task_without_time_tracking()
        tasks = [task]
        parameters = ForecastParametersBuilder.default_parameters().build()
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        self.assertIsNotNone(result[0].forecast)
        self.assertIsNotNone(result[0].forecast.target.health_status)
    


if __name__ == '__main__':
    unittest.main()