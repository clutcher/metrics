import unittest

from ui_web.convertors.developer_velocity_summary_convertor import DeveloperVelocitySummaryConvertor
from ui_web.data.hierarchical_item_data import HierarchicalItemData
from ui_web.data.task_data import AssignmentData, TimeTrackingData, SystemMetadataData
from ui_web.data.velocity_task_detail_data import TaskVelocityData


class TestDeveloperVelocitySummaryConvertorCalculation(unittest.TestCase):

    def test_shouldCalculateVelocityFromStoryPointsAndTimeSpent(self):
        # Given
        ideal_hours_per_day = 4.0
        convertor = DeveloperVelocitySummaryConvertor(ideal_hours_per_day)
        groups = [_build_group("Alice", [
            _build_task_velocity("TASK-1", developer_sp=3.0, developer_hours=8.0),
            _build_task_velocity("TASK-2", developer_sp=5.0, developer_hours=12.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        summary = result[0].summary
        self.assertAlmostEqual(8.0, summary.total_story_points, places=1)
        self.assertAlmostEqual(20.0, summary.total_time_hours, places=1)
        expected_velocity = 8.0 / (20.0 / 4.0)
        self.assertAlmostEqual(expected_velocity, summary.velocity, places=2)

    def test_shouldReturnNoneVelocityWhenDeveloperHasZeroHours(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(ideal_hours_per_day=4.0)
        groups = [_build_group("Bob", [
            _build_task_velocity("TASK-1", developer_sp=5.0, developer_hours=0.0),
        ])]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        self.assertIsNone(result[0].summary.velocity)

    def test_shouldEnrichAllGroupsWithSummaries(self):
        # Given
        convertor = DeveloperVelocitySummaryConvertor(ideal_hours_per_day=4.0)
        groups = [
            _build_group("Alice", [
                _build_task_velocity("TASK-1", developer_sp=4.0, developer_hours=8.0),
            ]),
            _build_group("Bob", [
                _build_task_velocity("TASK-2", developer_sp=6.0, developer_hours=16.0),
            ]),
        ]

        # When
        result = convertor.enrich_with_summaries(groups)

        # Then
        self.assertIsNotNone(result[0].summary)
        self.assertIsNotNone(result[1].summary)
        self.assertAlmostEqual(4.0, result[0].summary.total_story_points, places=1)
        self.assertAlmostEqual(6.0, result[1].summary.total_story_points, places=1)


def _build_task_velocity(task_id, developer_sp, developer_hours):
    return TaskVelocityData(
        id=task_id,
        title=f"Task {task_id}",
        assignment=AssignmentData(),
        time_tracking=TimeTrackingData(),
        system_metadata=SystemMetadataData(original_status="Done"),
        developer_story_points=developer_sp,
        developer_time_hours=developer_hours
    )


def _build_group(name, tasks):
    return HierarchicalItemData(
        name=name,
        type="developer",
        count=len(tasks),
        items=tasks
    )
