import unittest

from sd_metrics_lib.utils.time import Duration, TimeUnit

from velocity.app.domain.calculation.proxy_extractors import (
    extract_story_points, 
    extract_worklog_by_assignee, 
    extract_total_spent_time
)
from velocity.tests.fixtures.velocity_builders import TaskBuilder


class TestProxyExtractors(unittest.TestCase):

    def test_shouldExtractStoryPointsFromSprintPlanningTask(self):
        task = TaskBuilder.sprint_task().with_story_points(8.0).build()
        
        result = extract_story_points(task)
        
        self.assertEqual(8.0, result)

    def test_shouldReturnZeroStoryPointsWhenCapacityPlanningTaskHasNone(self):
        task = TaskBuilder.capacity_planning_task().build()
        
        result = extract_story_points(task)
        
        self.assertEqual(0.0, result)

    def test_shouldExtractWorklogFromRetrospectiveTaskWithTimeTracking(self):
        task = (TaskBuilder.retrospective_task()
                .assigned_to_senior_developer()
                .with_time_spent(6.0)
                .build())
        
        result = extract_worklog_by_assignee(task)
        
        self.assertEqual(1, len(result))
        self.assertEqual(Duration.of(6.0, TimeUnit.HOUR), result["senior-dev"])

    def test_shouldReturnEmptyWorklogWhenSprintTaskHasNoTimeTracking(self):
        task = (TaskBuilder.sprint_task()
                .assigned_to_junior_developer()
                .with_no_time_tracking()
                .build())
        
        result = extract_worklog_by_assignee(task)
        
        self.assertEqual({}, result)

    def test_shouldExtractTotalSpentTimeFromCapacityPlanningTask(self):
        task = (TaskBuilder.capacity_planning_task()
                .assigned_to_senior_developer()
                .with_time_spent(12.5)
                .build())
        
        result = extract_total_spent_time(task)
        
        self.assertEqual(Duration.of(12.5, TimeUnit.HOUR), result)

    def test_shouldReturnZeroDurationWhenRetrospectiveTaskHasNoTimeTracking(self):
        task = (TaskBuilder.retrospective_task()
                .assigned_to_junior_developer()
                .with_no_time_tracking()
                .build())
        
        result = extract_total_spent_time(task)
        
        self.assertEqual(Duration.zero(), result)

    def test_shouldExtractDistributedWorklogFromSprintTaskWithMultipleAssignees(self):
        task = (TaskBuilder.sprint_task()
                .with_distributed_time_spent({"alice": 4.0, "bob": 6.0})
                .build())
        
        result = extract_worklog_by_assignee(task)
        
        self.assertEqual(2, len(result))
        self.assertEqual(Duration.of(4.0, TimeUnit.HOUR), result["alice"])
        self.assertEqual(Duration.of(6.0, TimeUnit.HOUR), result["bob"])


if __name__ == '__main__':
    unittest.main()