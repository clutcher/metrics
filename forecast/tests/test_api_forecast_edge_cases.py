import unittest
from unittest.mock import AsyncMock

from sd_metrics_lib.utils.time import TimePolicy

from forecast.app.domain.forecast_service import ForecastService
from forecast.app.domain.model.config import ForecastConfig, CalculationConfig, SeniorityConfig
from forecast.tests.fixtures.forecast_builders import ForecastParametersBuilder, BusinessVelocityScenarios
from forecast.tests.fixtures.task_builders import TaskBuilder, BusinessScenarios
from forecast.tests.mocks.mock_task_repository import MockTaskRepository
from forecast.tests.mocks.mock_velocity_repository import MockVelocityRepository


class TestApiForecastEdgeCases(unittest.IsolatedAsyncioTestCase):
    
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
    
    async def test_shouldReturnOriginalTasksWhenVelocityDataUnavailable(self):
        task = BusinessScenarios.green_health_task()
        tasks = [task]
        parameters = ForecastParametersBuilder.default_parameters().build()
        
        self.task_repository.mock.get_tasks.return_value = tasks
        
        # Test None velocity
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.no_velocity_available()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        self.assertEqual(task.id, result[0].id)
        self.assertEqual(task.title, result[0].title)
        self.assertIsNone(result[0].forecast)
        
        # Test negative velocity
        self.velocity_repository.mock.get_velocity.return_value = -1.0
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        self.assertIsNone(result[0].forecast)
        
        # Test zero velocity  
        self.velocity_repository.mock.get_velocity.return_value = 0.0
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        self.assertIsNone(result[0].forecast)
    
    async def test_shouldHandleEmptyTaskListGracefully(self):
        empty_tasks = []
        parameters = ForecastParametersBuilder.default_parameters().build()
        
        self.task_repository.mock.get_tasks.return_value = empty_tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(empty_tasks, parameters)
        
        self.assertEqual(0, len(result))
    
    async def test_shouldHandleTasksWithoutStoryPointsInAggregation(self):
        child_with_story_points = (TaskBuilder("CHILD-1", "Valid Child Task")
                                  .with_story_points(5.0)
                                  .assigned_to_senior_developer()
                                  .with_no_time_spent()
                                  .build())
        
        child_without_story_points = (TaskBuilder("CHILD-2", "Invalid Child Task")
                                     .assigned_to_junior_developer()
                                     .with_no_time_spent()
                                     .build())
        
        parent_task = (TaskBuilder("PARENT-1", "Mixed Children Parent")
                       .assigned_to_senior_developer()
                       .with_no_time_spent()
                       .with_child_tasks(child_with_story_points, child_without_story_points)
                       .build())
        
        tasks = [parent_task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .with_cumulative_story_points()
                     .build())
        
        self.task_repository.mock.get_tasks_with_full_hierarchy.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        parent = result[0]
        child1 = parent.child_tasks[0]
        child2 = parent.child_tasks[1]
        
        self.assertIsNotNone(child1.forecast)
        self.assertIsNone(child2.forecast)
        
        self.assertIsNotNone(parent.forecast)
        expected_parent_estimation = 5.0 / 1.5
        self.assertAlmostEqual(expected_parent_estimation, parent.forecast.estimation_time.time_delta, places=2)
    
    
    
    
    async def test_shouldHandleGenerateForecastsForTaskIdsWithEmptyList(self):
        empty_task_ids = []
        parameters = ForecastParametersBuilder.default_parameters().build()
        
        self.task_repository.mock.get_tasks.return_value = []
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_task_ids(empty_task_ids, parameters)
        
        self.assertEqual(0, len(result))
        self.task_repository.mock.get_tasks.assert_called_once_with([])
    
    async def test_shouldHandleTaskWithAllNullOptionalFields(self):
        task = (TaskBuilder("NULL-TASK", "Task with null fields")
                .build())
        tasks = [task]
        parameters = ForecastParametersBuilder.default_parameters().build()
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        self.assertEqual("NULL-TASK", result[0].id)
        self.assertEqual("Task with null fields", result[0].title)
        self.assertIsNone(result[0].forecast)
    
    async def test_shouldHandleMixedValidAndInvalidTasks(self):
        valid_task = BusinessScenarios.green_health_task()
        invalid_task = BusinessScenarios.task_without_story_points()
        tasks = [valid_task, invalid_task]
        parameters = ForecastParametersBuilder.default_parameters().build()
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(2, len(result))
        self.assertIsNotNone(result[0].forecast)
        self.assertIsNone(result[1].forecast)


if __name__ == '__main__':
    unittest.main()