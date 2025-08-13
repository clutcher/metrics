import unittest
from unittest.mock import AsyncMock

from sd_metrics_lib.utils.time import TimePolicy, TimeUnit

from forecast.app.domain.forecast_service import ForecastService
from forecast.app.domain.model.config import ForecastConfig, CalculationConfig, SeniorityConfig
from forecast.tests.fixtures.forecast_builders import ForecastParametersBuilder, BusinessVelocityScenarios
from forecast.tests.fixtures.task_builders import TaskBuilder, BusinessScenarios
from forecast.tests.mocks.mock_task_repository import MockTaskRepository
from forecast.tests.mocks.mock_velocity_repository import MockVelocityRepository


class TestApiForecastEstimation(unittest.IsolatedAsyncioTestCase):
    
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
    
    async def test_shouldGenerateForecastWithEstimationTimeWhenTaskHasStoryPoints(self):
        task = (TaskBuilder.authentication_feature()
                .with_story_points(8.0)
                .assigned_to_senior_developer()
                .with_no_time_spent()
                .build())
        tasks = [task]
        parameters = ForecastParametersBuilder.default_parameters().in_hours().build()
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        forecast = result[0].forecast
        self.assertIsNotNone(forecast)
        self.assertIsNotNone(forecast.estimation_time)
        self.assertEqual(TimeUnit.HOUR, forecast.estimation_time.time_unit)
    
    async def test_shouldGenerateForecastWithRequestedTimeUnit(self):
        task = (TaskBuilder.new_feature()
                .with_story_points(12.0)
                .assigned_to_junior_developer()
                .with_no_time_spent()
                .build())
        tasks = [task]
        parameters = ForecastParametersBuilder.default_parameters().in_days().build()
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.senior_developer_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        forecast = result[0].forecast
        self.assertIsNotNone(forecast)
        self.assertIsNotNone(forecast.estimation_time)
        self.assertEqual(TimeUnit.DAY, forecast.estimation_time.time_unit)
    
    
    async def test_shouldStoreVelocityUsedInForecast(self):
        task = (TaskBuilder.authentication_feature()
                .with_story_points(6.0)
                .assigned_to_senior_developer()
                .with_no_time_spent()
                .build())
        tasks = [task]
        parameters = ForecastParametersBuilder.default_parameters().build()
        
        expected_velocity = 2.5
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity.return_value = expected_velocity
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        forecast = result[0].forecast
        self.assertIsNotNone(forecast)
        self.assertEqual(expected_velocity, forecast.velocity)


if __name__ == '__main__':
    unittest.main()