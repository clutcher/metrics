import unittest
from datetime import datetime

from sd_metrics_lib.utils.time import Duration, TimeUnit

from tasks.app.domain.model.task import Task, Assignment, Assignee, TimeTracking, SystemMetadata
from ui_web.convertors.velocity_task_detail_convertor import VelocityTaskDetailConvertor


class TestVelocityTaskDetailConvertorDeveloperBreakdown(unittest.TestCase):

    def test_shouldSplitStoryPointsProportionallyWhenTwoDevelopersShareTask(self):
        # Given
        task = _build_task(
            "TASK-1", "Shared feature implementation",
            story_points=10.0,
            time_by_assignee={"alice": 21600, "bob": 14400}
        )

        # When
        result = VelocityTaskDetailConvertor.convert_tasks_to_developers_breakdown(
            [task], ["alice", "bob"]
        )

        # Then
        alice_entry = next(r for r in result if r.assignment.assignee.id == "alice")
        bob_entry = next(r for r in result if r.assignment.assignee.id == "bob")
        self.assertAlmostEqual(6.0, alice_entry.developer_story_points, places=1)
        self.assertAlmostEqual(4.0, bob_entry.developer_story_points, places=1)

    def test_shouldSkipTasksWithZeroStoryPoints(self):
        # Given
        task = _build_task(
            "TASK-1", "Task with zero SP",
            story_points=0.0,
            time_by_assignee={"alice": 18000}
        )

        # When
        result = VelocityTaskDetailConvertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"]
        )

        # Then
        self.assertEqual(0, len(result))

    def test_shouldSkipTasksWithMissingStoryPoints(self):
        # Given
        task = _build_task(
            "TASK-1", "Task without SP",
            story_points=None,
            time_by_assignee={"alice": 18000}
        )

        # When
        result = VelocityTaskDetailConvertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"]
        )

        # Then
        self.assertEqual(0, len(result))

    def test_shouldSkipTasksWithNoTimeTrackingData(self):
        # Given
        task = _build_task("TASK-1", "Task without time tracking", story_points=5.0)

        # When
        result = VelocityTaskDetailConvertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"]
        )

        # Then
        self.assertEqual(0, len(result))

    def test_shouldOnlyIncludeEntriesForDevelopersWhoHaveLoggedTime(self):
        # Given
        task = _build_task(
            "TASK-1", "Alice-only task",
            story_points=8.0,
            time_by_assignee={"alice": 36000}
        )

        # When
        result = VelocityTaskDetailConvertor.convert_tasks_to_developers_breakdown(
            [task], ["alice", "bob"]
        )

        # Then
        self.assertEqual(1, len(result))
        self.assertEqual("alice", result[0].assignment.assignee.id)

    def test_shouldReturnEmptyStatusWhenSystemMetadataIsMissing(self):
        # Given
        task = _build_task(
            "TASK-1", "Task without metadata",
            story_points=5.0,
            time_by_assignee={"alice": 10800},
            system_metadata=None
        )

        # When
        result = VelocityTaskDetailConvertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"]
        )

        # Then
        self.assertEqual("", result[0].system_metadata.original_status)

    def test_shouldCalculateDeveloperTimeInHours(self):
        # Given
        task = _build_task(
            "TASK-1", "Time tracking task",
            story_points=5.0,
            time_by_assignee={"alice": 57600}
        )

        # When
        result = VelocityTaskDetailConvertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"]
        )

        # Then
        self.assertAlmostEqual(16.0, result[0].developer_time_hours, places=1)


def _build_task(task_id, title, story_points=None, time_by_assignee=None, system_metadata="default"):
    time_tracking = TimeTracking()
    if time_by_assignee:
        assignee_durations = {
            name: Duration.of(seconds, TimeUnit.SECOND)
            for name, seconds in time_by_assignee.items()
        }
        total_seconds = sum(time_by_assignee.values())
        time_tracking = TimeTracking(
            total_spent_time=Duration.of(total_seconds, TimeUnit.SECOND),
            spent_time_by_assignee=assignee_durations
        )

    if system_metadata == "default":
        system_metadata = SystemMetadata(original_status="In Progress", project_key="PROJ")

    return Task(
        id=task_id,
        title=title,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 15),
        system_metadata=system_metadata,
        assignment=Assignment(),
        time_tracking=time_tracking,
        story_points=story_points
    )
