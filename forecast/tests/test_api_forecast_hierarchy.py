import unittest
from unittest.mock import AsyncMock

from sd_metrics_lib.utils.time import TimePolicy, TimeUnit

from forecast.app.domain.forecast_service import ForecastService
from forecast.app.domain.model.config import ForecastConfig, CalculationConfig, SeniorityConfig
from forecast.app.domain.model.enums import StoryPointsStrategy
from forecast.tests.fixtures.forecast_builders import ForecastParametersBuilder, BusinessVelocityScenarios
from forecast.tests.fixtures.task_builders import TaskBuilder, BusinessScenarios
from forecast.tests.mocks.mock_task_repository import MockTaskRepository
from forecast.tests.mocks.mock_velocity_repository import MockVelocityRepository


class TestApiForecastHierarchy(unittest.IsolatedAsyncioTestCase):
    
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
    
    async def test_shouldGenerateDirectForecastsOnlyWhenUsingDirectStrategy(self):
        parent_task = BusinessScenarios.parent_task_with_children()
        tasks = [parent_task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .with_direct_story_points()
                     .build())
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        parent = result[0]
        self.assertIsNotNone(parent.forecast)
        
        expected_parent_estimation = 10.0 / 1.5
        self.assertAlmostEqual(expected_parent_estimation, parent.forecast.estimation_time.time_delta, places=2)
        
        child1 = parent.child_tasks[0]
        child2 = parent.child_tasks[1]
        self.assertIsNotNone(child1.forecast)
        self.assertIsNotNone(child2.forecast)
        
        expected_child1_estimation = 3.0 / 1.5
        expected_child2_estimation = 5.0 / 1.5
        self.assertAlmostEqual(expected_child1_estimation, child1.forecast.estimation_time.time_delta, places=2)
        self.assertAlmostEqual(expected_child2_estimation, child2.forecast.estimation_time.time_delta, places=2)
    
    async def test_shouldAggregateChildTasksBottomUpWhenUsingCumulativeStrategy(self):
        child1 = (TaskBuilder("CHILD-1", "Child Task 1")
                  .with_story_points(4.0)
                  .assigned_to_senior_developer()
                  .with_no_time_spent()
                  .build())
        
        child2 = (TaskBuilder("CHILD-2", "Child Task 2")
                  .with_story_points(6.0)
                  .assigned_to_junior_developer()
                  .with_no_time_spent()
                  .build())
        
        parent_task = (TaskBuilder("PARENT-1", "Parent Task Without Story Points")
                       .assigned_to_senior_developer()
                       .with_no_time_spent()
                       .with_child_tasks(child1, child2)
                       .build())
        
        tasks = [parent_task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .with_cumulative_story_points()
                     .in_hours()
                     .build())
        
        self.task_repository.mock.get_tasks_with_full_hierarchy.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        parent = result[0]
        self.assertIsNotNone(parent.forecast)
        
        child1_estimation = 4.0 / 1.5
        child2_estimation = 6.0 / 1.5
        expected_parent_estimation = child1_estimation + child2_estimation
        
        self.assertAlmostEqual(expected_parent_estimation, parent.forecast.estimation_time.time_delta, places=2)
    
    async def test_shouldSkipParentAggregationWhenParentHasDirectEstimation(self):
        child1 = (TaskBuilder("CHILD-1", "Child Task 1")
                  .with_story_points(3.0)
                  .assigned_to_senior_developer()
                  .with_no_time_spent()
                  .build())
        
        child2 = (TaskBuilder("CHILD-2", "Child Task 2")
                  .with_story_points(5.0)
                  .assigned_to_junior_developer()
                  .with_no_time_spent()
                  .build())
        
        parent_task = (TaskBuilder("PARENT-1", "Parent Task With Direct Story Points")
                       .with_story_points(12.0)
                       .assigned_to_senior_developer()
                       .with_no_time_spent()
                       .with_child_tasks(child1, child2)
                       .build())
        
        tasks = [parent_task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .with_cumulative_story_points()
                     .in_hours()
                     .build())
        
        self.task_repository.mock.get_tasks_with_full_hierarchy.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        parent = result[0]
        self.assertIsNotNone(parent.forecast)
        
        expected_direct_estimation = 12.0 / 1.5
        self.assertAlmostEqual(expected_direct_estimation, parent.forecast.estimation_time.time_delta, places=2)
        
        child1_estimation = 3.0 / 1.5
        child2_estimation = 5.0 / 1.5
        aggregated_estimation = child1_estimation + child2_estimation
        
        self.assertNotAlmostEqual(aggregated_estimation, parent.forecast.estimation_time.time_delta, places=2)
    
    async def test_shouldCalculateParentEstimationFromChildrenSum(self):
        child1 = (TaskBuilder("CHILD-1", "Backend API Task")
                  .with_story_points(8.0)
                  .assigned_to_senior_developer()
                  .with_no_time_spent()
                  .build())
        
        child2 = (TaskBuilder("CHILD-2", "Frontend UI Task")
                  .with_story_points(5.0)
                  .assigned_to_junior_developer()
                  .with_no_time_spent()
                  .build())
        
        child3 = (TaskBuilder("CHILD-3", "Testing Task")
                  .with_story_points(3.0)
                  .assigned_to_senior_developer()
                  .with_no_time_spent()
                  .build())
        
        parent_task = (TaskBuilder("EPIC-1", "Complete Feature Epic")
                       .assigned_to_senior_developer()
                       .with_no_time_spent()
                       .with_child_tasks(child1, child2, child3)
                       .build())
        
        tasks = [parent_task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .with_cumulative_story_points()
                     .in_hours()
                     .build())
        
        self.task_repository.mock.get_tasks_with_full_hierarchy.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.high_performing_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        parent = result[0]
        self.assertIsNotNone(parent.forecast)
        
        total_story_points = 8.0 + 5.0 + 3.0
        expected_aggregated_estimation = total_story_points / 2.5
        
        self.assertAlmostEqual(expected_aggregated_estimation, parent.forecast.estimation_time.time_delta, places=2)
        
        for child_task in parent.child_tasks:
            self.assertIsNotNone(child_task.forecast)
    
    async def test_shouldHandleDeepTaskHierarchyWithCumulativeStrategy(self):
        grandchild = (TaskBuilder("GRANDCHILD-1", "Detailed Implementation")
                      .with_story_points(2.0)
                      .assigned_to_junior_developer()
                      .with_no_time_spent()
                      .build())
        
        child = (TaskBuilder("CHILD-1", "Feature Component")
                 .with_story_points(4.0)
                 .assigned_to_senior_developer()
                 .with_no_time_spent()
                 .with_child_tasks(grandchild)
                 .build())
        
        parent_task = (TaskBuilder("PARENT-1", "Major Feature")
                       .assigned_to_senior_developer()
                       .with_no_time_spent()
                       .with_child_tasks(child)
                       .build())
        
        tasks = [parent_task]
        parameters = (ForecastParametersBuilder.default_parameters()
                     .with_cumulative_story_points()
                     .in_hours()
                     .build())
        
        self.task_repository.mock.get_tasks_with_full_hierarchy.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        result = await self.forecast_service.generate_forecasts_for_tasks(tasks, parameters)
        
        parent = result[0]
        child = parent.child_tasks[0]
        grandchild = child.child_tasks[0]
        
        self.assertIsNotNone(grandchild.forecast)
        self.assertIsNotNone(child.forecast)
        self.assertIsNotNone(parent.forecast)
        
        expected_grandchild_estimation = 2.0 / 1.5
        expected_child_direct_estimation = 4.0 / 1.5
        expected_parent_aggregated_estimation = expected_child_direct_estimation
        
        self.assertAlmostEqual(expected_grandchild_estimation, grandchild.forecast.estimation_time.time_delta, places=2)
        self.assertAlmostEqual(expected_child_direct_estimation, child.forecast.estimation_time.time_delta, places=2)
        self.assertAlmostEqual(expected_parent_aggregated_estimation, parent.forecast.estimation_time.time_delta, places=2)
    
    async def test_shouldUseCorrectRepositoryMethodBasedOnStrategy(self):
        task = BusinessScenarios.green_health_task()
        tasks = [task]
        
        direct_parameters = (ForecastParametersBuilder.default_parameters()
                           .with_direct_story_points()
                           .build())
        
        cumulative_parameters = (ForecastParametersBuilder.default_parameters()
                               .with_cumulative_story_points()
                               .build())
        
        self.task_repository.mock.get_tasks.return_value = tasks
        self.task_repository.mock.get_tasks_with_full_hierarchy.return_value = tasks
        self.velocity_repository.mock.get_velocity = AsyncMock(
            return_value=BusinessVelocityScenarios.average_team_velocity()
        )
        
        await self.forecast_service.generate_forecasts_for_task_ids(["AUTH-123"], direct_parameters)
        await self.forecast_service.generate_forecasts_for_task_ids(["AUTH-123"], cumulative_parameters)
        
        self.task_repository.mock.get_tasks.assert_called_once_with(["AUTH-123"])
        self.task_repository.mock.get_tasks_with_full_hierarchy.assert_called_once_with(["AUTH-123"])


if __name__ == '__main__':
    unittest.main()