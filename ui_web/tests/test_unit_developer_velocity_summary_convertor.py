import unittest

from ui_web.convertors.developer_velocity_summary_convertor import DeveloperVelocitySummaryConvertor
from ui_web.data.hierarchical_item_data import HierarchicalItemData
from ui_web.data.task_data import AssignmentData, TimeTrackingData, SystemMetadataData
from ui_web.data.velocity_task_detail_data import TaskVelocityData


class TestDeveloperVelocitySummaryConvertorCalculation(unittest.TestCase):

    def test_shouldCalculateVelocityFromStoryPointsAndTimeDays(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [_build_group("Alice", [
            _build_task_velocity("TASK-1", developer_sp=3.0, developer_days=2.0),
            _build_task_velocity("TASK-2", developer_sp=5.0, developer_days=3.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        summary = result[0].summary
        self.assertAlmostEqual(8.0, summary.total_story_points, places=1)
        self.assertAlmostEqual(5.0, summary.total_time_days, places=1)
        expected_velocity = 8.0 / 5.0
        self.assertAlmostEqual(expected_velocity, summary.velocity, places=2)

    def test_shouldReturnNoneVelocityWhenDeveloperHasZeroDays(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [_build_group("Bob", [
            _build_task_velocity("TASK-1", developer_sp=5.0, developer_days=0.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        self.assertIsNone(result[0].summary.velocity)

    def test_shouldEnrichAllGroupsWithSummaries(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [
            _build_group("Alice", [
                _build_task_velocity("TASK-1", developer_sp=4.0, developer_days=2.0),
            ]),
            _build_group("Bob", [
                _build_task_velocity("TASK-2", developer_sp=6.0, developer_days=4.0),
            ]),
        ]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        self.assertIsNotNone(result[0].summary)
        self.assertIsNotNone(result[1].summary)
        self.assertAlmostEqual(4.0, result[0].summary.total_story_points, places=1)
        self.assertAlmostEqual(6.0, result[1].summary.total_story_points, places=1)


class TestDeveloperVelocitySummaryConvertorWorkload(unittest.TestCase):

    def test_shouldCalculateWorkloadPercentFromWorkingDaysAndMonthDays(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [_build_group("Alice", [
            _build_task_velocity("TASK-1", developer_sp=3.0, developer_days=11.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        summary = result[0].summary
        self.assertAlmostEqual(11.0, summary.working_days, places=1)
        self.assertEqual(22, summary.working_days_in_month)
        self.assertAlmostEqual(50.0, summary.workload_percent, places=0)

    def test_shouldCalculateTotalEstimatedDaysAsSumOfTaskEstimates(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [_build_group("Alice", [
            _build_task_velocity("TASK-1", developer_sp=3.0, developer_days=2.0,
                                 estimated_days=2.0),
            _build_task_velocity("TASK-2", developer_sp=5.0, developer_days=3.0,
                                 estimated_days=3.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        self.assertAlmostEqual(5.0, result[0].summary.total_estimated_days, places=1)

    def test_shouldCalculateAverageDeviationPercentFromPreComputedTaskValues(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [_build_group("Alice", [
            _build_task_velocity("TASK-1", developer_sp=3.0, developer_days=1.0,
                                 estimated_days=2.0, deviation_percent=50.0),
            _build_task_velocity("TASK-2", developer_sp=5.0, developer_days=6.0,
                                 estimated_days=4.0, deviation_percent=-50.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        expected_avg = (50.0 + (-50.0)) / 2
        self.assertAlmostEqual(expected_avg, result[0].summary.average_deviation_percent, places=1)

    def test_shouldSumTotalTaskStoryPointsFromAllTasks(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [_build_group("Alice", [
            _build_task_velocity("TASK-1", developer_sp=3.0, developer_days=2.0,
                                 story_points=8.0),
            _build_task_velocity("TASK-2", developer_sp=5.0, developer_days=3.0,
                                 story_points=5.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        self.assertAlmostEqual(13.0, result[0].summary.total_task_story_points, places=1)

    def test_shouldReturnNoneTotalTaskStoryPointsWhenNoTasksHaveStoryPoints(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [_build_group("Alice", [
            _build_task_velocity("TASK-1", developer_sp=3.0, developer_days=2.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        self.assertIsNone(result[0].summary.total_task_story_points)

    def test_shouldReturnNoneEstimatedDaysWhenNoTasksHaveEstimation(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(working_days_per_month=22)
        groups = [_build_group("Alice", [
            _build_task_velocity("TASK-1", developer_sp=3.0, developer_days=2.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        self.assertIsNone(result[0].summary.total_estimated_days)
        self.assertIsNone(result[0].summary.average_deviation_percent)


def _build_task_velocity(task_id, developer_sp, developer_days,
                         story_points=None, estimated_days=None,
                         deviation_percent=None):
    return TaskVelocityData(
        id=task_id,
        title=f"Task {task_id}",
        assignment=AssignmentData(),
        time_tracking=TimeTrackingData(),
        system_metadata=SystemMetadataData(original_status="Done"),
        story_points=story_points,
        developer_story_points=developer_sp,
        developer_time_days=developer_days,
        estimated_days=estimated_days,
        deviation_percent=deviation_percent
    )


def _build_group(name, tasks):
    return HierarchicalItemData(
        name=name,
        type="developer",
        count=len(tasks),
        items=tasks
    )
