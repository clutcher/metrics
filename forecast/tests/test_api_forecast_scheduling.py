import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from sd_metrics_lib.utils.time import TimePolicy, TimeUnit

from forecast.app.domain.forecast_service import ForecastService
from forecast.app.domain.model.config import ForecastConfig, CalculationConfig, SeniorityConfig
from forecast.app.domain.model.enums import VelocityStrategy
from forecast.tests.fixtures.forecast_builders import ForecastParametersBuilder, BusinessVelocityScenarios
from forecast.tests.fixtures.task_builders import TaskBuilder, BusinessScenarios
from forecast.tests.mocks.mock_task_repository import MockTaskRepository
from forecast.tests.mocks.mock_velocity_repository import MockVelocityRepository


class TestApiForecastScheduling(unittest.IsolatedAsyncioTestCase):
    
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
    
    async def test_shouldCalculateSequentialStartAndEndDatesForSingleTask(self):
        sprint_start = datetime(2024, 2, 5, 9, 0, 0)
        task = (TaskBuilder.authentication_feature()
                .with_story_points(8.0)
                .assigned_to_senior_developer()
                .with_no_time_spent()
                .build())
        tasks = [task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .starting_on(sprint_start)
                     .in_days()
                     .using_real_velocity()
                     .build())
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        task_forecast = result[0].forecast
        self.assertIsNotNone(task_forecast)
        self.assertEqual(sprint_start, task_forecast.start_date)
        
        expected_duration_days = 8.0 / 1.5
        expected_end_date = sprint_start + timedelta(days=expected_duration_days)
        self.assertEqual(expected_end_date, task_forecast.end_date)
    
    async def test_shouldScheduleChildTasksBeforeParentCompletion(self):
        sprint_start = datetime(2024, 2, 5, 9, 0, 0)
        
        child1 = (TaskBuilder("AUTH-124", "Design login UI")
                  .with_story_points(3.0)
                  .assigned_to_senior_developer()
                  .with_no_time_spent()
                  .build())
        
        child2 = (TaskBuilder("AUTH-125", "Implement authentication API")
                  .with_story_points(5.0)
                  .assigned_to_junior_developer()
                  .with_no_time_spent()
                  .build())
        
        parent_task = (TaskBuilder.epic_with_children()
                       .with_story_points(10.0)
                       .assigned_to_senior_developer()
                       .with_no_time_spent()
                       .with_child_tasks(child1, child2)
                       .build())
        
        tasks = [parent_task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .starting_on(sprint_start)
                     .in_days()
                     .using_real_velocity()
                     .build())
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        parent = result[0]
        child1_forecast = parent.child_tasks[0].forecast
        child2_forecast = parent.child_tasks[1].forecast
        parent_forecast = parent.forecast
        
        self.assertIsNotNone(child1_forecast)
        self.assertIsNotNone(child2_forecast)
        self.assertIsNotNone(parent_forecast)
        
        self.assertEqual(sprint_start, child1_forecast.start_date)
        self.assertEqual(sprint_start, parent_forecast.start_date)
        
        child1_expected_end = sprint_start + timedelta(days=3.0 / 1.5)
        self.assertEqual(child1_expected_end, child1_forecast.end_date)
        
        self.assertEqual(child1_expected_end, child2_forecast.start_date)
        
        child2_expected_end = child1_expected_end + timedelta(days=5.0 / 1.5)
        self.assertEqual(child2_expected_end, child2_forecast.end_date)
        
        self.assertEqual(child2_expected_end, parent_forecast.end_date)
    
    async def test_shouldHandleDifferentVelocityStrategiesForDateCalculation(self):
        sprint_start = datetime(2024, 2, 5, 9, 0, 0)
        task = (TaskBuilder.new_feature()
                .with_story_points(6.0)
                .assigned_to_senior_developer()
                .with_no_time_spent()
                .build())
        tasks = [task]
        
        real_velocity_params = (ForecastParametersBuilder.default_parameters()
                               .starting_on(sprint_start)
                               .in_days()
                               .using_real_velocity()
                               .build())
        
        ideal_velocity_params = (ForecastParametersBuilder.default_parameters()
                                .starting_on(sprint_start)
                                .in_days()
                                .using_ideal_velocity()
                                .build())
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        real_result = await self.forecast_service.generate_forecasts_for_tasks(tasks, real_velocity_params)
        ideal_result = await self.forecast_service.generate_forecasts_for_tasks(tasks, ideal_velocity_params)
        
        real_forecast = real_result[0].forecast
        ideal_forecast = ideal_result[0].forecast
        
        self.assertIsNotNone(real_forecast)
        self.assertIsNotNone(ideal_forecast)
        
        self.assertEqual(sprint_start, real_forecast.start_date)
        self.assertEqual(sprint_start, ideal_forecast.start_date)
        
        expected_duration_days = 6.0 / 1.5
        expected_end_date = sprint_start + timedelta(days=expected_duration_days)
        
        self.assertEqual(expected_end_date, real_forecast.end_date)
        self.assertEqual(expected_end_date, ideal_forecast.end_date)
    
    async def test_shouldConvertEstimationTimeToBusinessDaysCorrectly(self):
        project_start = datetime(2024, 3, 1, 8, 0, 0)
        task = (TaskBuilder.critical_bug()
                .with_story_points(12.0)
                .assigned_to_senior_developer()
                .with_no_time_spent()
                .build())
        tasks = [task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .starting_on(project_start)
                     .in_hours()
                     .using_real_velocity()
                     .build())
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.senior_developer_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        task_forecast = result[0].forecast
        self.assertIsNotNone(task_forecast)
        
        self.assertEqual(project_start, task_forecast.start_date)
        
        estimated_hours = 12.0 / 3.0
        self.assertAlmostEqual(estimated_hours, task_forecast.estimation_time.time_delta, places=2)

        expected_end_date = project_start + timedelta(hours=estimated_hours)
        
        self.assertEqual(expected_end_date, task_forecast.end_date)
    
    async def test_shouldHandleZeroDurationTasksGracefully(self):
        sprint_start = datetime(2024, 2, 5, 9, 0, 0)
        task = BusinessScenarios.task_without_story_points()
        tasks = [task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .starting_on(sprint_start)
                     .in_days()
                     .build())
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        self.assertEqual(1, len(result))
        self.assertIsNone(result[0].forecast)
    
    async def test_shouldScheduleMultipleSequentialTasks(self):
        sprint_start = datetime(2024, 2, 5, 9, 0, 0)
        
        task1 = (TaskBuilder("TASK-1", "First Task")
                 .with_story_points(4.0)
                 .assigned_to_senior_developer()
                 .with_no_time_spent()
                 .build())
        
        task2 = (TaskBuilder("TASK-2", "Second Task")
                 .with_story_points(6.0)
                 .assigned_to_junior_developer()
                 .with_no_time_spent()
                 .build())
        
        parent_task = (TaskBuilder("EPIC-1", "Sequential Epic")
                       .assigned_to_senior_developer()
                       .with_no_time_spent()
                       .with_child_tasks(task1, task2)
                       .build())
        
        tasks = [parent_task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .starting_on(sprint_start)
                     .in_days()
                     .with_cumulative_story_points()
                     .build())
        
        self.task_repository.mock.get_tasks_with_full_hierarchy.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        parent = result[0]
        task1_forecast = parent.child_tasks[0].forecast
        task2_forecast = parent.child_tasks[1].forecast
        parent_forecast = parent.forecast
        
        self.assertEqual(sprint_start, task1_forecast.start_date)
        
        task1_duration = 4.0 / 1.5
        task1_end = sprint_start + timedelta(days=task1_duration)
        self.assertEqual(task1_end, task1_forecast.end_date)
        
        self.assertEqual(task1_end, task2_forecast.start_date)
        
        task2_duration = 6.0 / 1.5
        task2_end = task1_end + timedelta(days=task2_duration)
        self.assertEqual(task2_end, task2_forecast.end_date)
        
        self.assertEqual(sprint_start, parent_forecast.start_date)
        self.assertEqual(task2_end, parent_forecast.end_date)
    
    async def test_shouldHandleIdealVelocityTimeConversion(self):
        project_start = datetime(2024, 4, 1, 9, 0, 0)
        task = (TaskBuilder.authentication_feature()
                .with_story_points(16.0)
                .assigned_to_senior_developer()
                .with_no_time_spent()
                .build())
        tasks = [task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .starting_on(project_start)
                     .in_hours()
                     .using_ideal_velocity()
                     .build())
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.high_performing_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        task_forecast = result[0].forecast
        self.assertIsNotNone(task_forecast)
        
        self.assertEqual(project_start, task_forecast.start_date)
        
        estimated_hours = 16.0 / 2.5
        self.assertAlmostEqual(estimated_hours, task_forecast.estimation_time.time_delta, places=2)
        
        business_days = estimated_hours / 8.0
        expected_end_date = project_start + timedelta(days=business_days)
        
        self.assertEqual(expected_end_date, task_forecast.end_date)


if __name__ == '__main__':
    unittest.main()