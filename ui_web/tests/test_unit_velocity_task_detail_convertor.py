import unittest

from sd_metrics_lib.utils.time import Duration, TimeUnit, TimePolicy

from tasks.app.domain.model.task import Task, Assignment, Assignee, TimeTracking, SystemMetadata
from ui_web.convertors.velocity_task_detail_convertor import VelocityTaskDetailConvertor


_TEST_TIME_POLICY = TimePolicy(hours_per_day=4.0, days_per_week=5, days_per_month=22)

_SENIOR_VELOCITY = 1.0
_MIDDLE_VELOCITY = 0.5
_JUNIOR_VELOCITY = 0.25


def _create_convertor(time_policy=_TEST_TIME_POLICY):
    return VelocityTaskDetailConvertor(time_policy=time_policy)


class TestVelocityTaskDetailConvertorDeveloperBreakdown(unittest.TestCase):

    def setUp(self):
        self.convertor = _create_convertor()
        self.velocities = {"alice": _SENIOR_VELOCITY, "bob": _MIDDLE_VELOCITY}

    def test_shouldSplitStoryPointsProportionallyWhenTwoDevelopersShareTask(self):
        # Given
        task = _build_task(
            "TASK-1", "Shared feature implementation",
            story_points=10.0,
            time_by_assignee={"alice": 21600, "bob": 14400}
        )

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice", "bob"], self.velocities
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
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], self.velocities
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
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], self.velocities
        )

        # Then
        self.assertEqual(0, len(result))

    def test_shouldSkipTasksWithNoTimeTrackingData(self):
        # Given
        task = _build_task("TASK-1", "Task without time tracking", story_points=5.0)

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], self.velocities
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
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice", "bob"], self.velocities
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
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], self.velocities
        )

        # Then
        self.assertEqual("", result[0].system_metadata.original_status)

    def test_shouldConvertDeveloperTimeToDays(self):
        # Given
        task = _build_task(
            "TASK-1", "Time tracking task",
            story_points=5.0,
            time_by_assignee={"alice": 57600}
        )

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], self.velocities
        )

        # Then
        self.assertAlmostEqual(4.0, result[0].developer_time_days, places=1)


class TestVelocityTaskDetailConvertorEstimation(unittest.TestCase):

    def setUp(self):
        self.convertor = _create_convertor()

    def test_shouldEstimateMoreDaysForSlowerDeveloperThanFasterOne(self):
        # Given
        task = _build_task(
            "TASK-1", "Feature implementation",
            story_points=8.0,
            time_by_assignee={"alice": 14400, "charlie": 14400}
        )
        velocities = {"alice": _SENIOR_VELOCITY, "charlie": _JUNIOR_VELOCITY}

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice", "charlie"], velocities
        )

        # Then
        alice_entry = next(r for r in result if r.assignment.assignee.id == "alice")
        charlie_entry = next(r for r in result if r.assignment.assignee.id == "charlie")
        self.assertLess(alice_entry.estimated_days, charlie_entry.estimated_days)

    def test_shouldCalculatePositiveDeviationWhenTaskCompletedFasterThanEstimated(self):
        # Given
        task = _build_task(
            "TASK-1", "Quick task",
            story_points=4.0,
            time_by_assignee={"alice": 3600}
        )
        velocities = {"alice": _MIDDLE_VELOCITY}

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], velocities
        )

        # Then
        self.assertGreater(result[0].deviation_percent, 0)

    def test_shouldCalculateNegativeDeviationWhenTaskTookLongerThanEstimated(self):
        # Given
        task = _build_task(
            "TASK-1", "Slow task",
            story_points=1.0,
            time_by_assignee={"alice": 57600}
        )
        velocities = {"alice": _SENIOR_VELOCITY}

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], velocities
        )

        # Then
        self.assertLess(result[0].deviation_percent, 0)

    def test_shouldReturnNoneWhenVelocityIsNotAvailable(self):
        # Given
        task = _build_task(
            "TASK-1", "Unknown dev task",
            story_points=4.0,
            time_by_assignee={"unknown_dev": 14400}
        )
        velocities = {"unknown_dev": None}

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["unknown_dev"], velocities
        )

        # Then
        self.assertIsNone(result[0].total_estimated_days)
        self.assertIsNone(result[0].estimated_days)
        self.assertIsNone(result[0].deviation_percent)

    def test_shouldCalculateDevEstimatedDaysFromProportionalStoryPoints(self):
        # Given
        task = _build_task(
            "TASK-1", "Estimation task",
            story_points=10.0,
            time_by_assignee={"alice": 14400}
        )
        velocities = {"alice": _MIDDLE_VELOCITY}

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], velocities
        )

        # Then
        self.assertAlmostEqual(10.0 / _MIDDLE_VELOCITY, result[0].estimated_days, places=1)

    def test_shouldCalculateTotalEstimatedDaysFromFullStoryPoints(self):
        # Given
        task = _build_task(
            "TASK-1", "Shared task",
            story_points=10.0,
            time_by_assignee={"alice": 21600, "bob": 14400}
        )
        velocities = {"alice": _MIDDLE_VELOCITY, "bob": _MIDDLE_VELOCITY}

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice", "bob"], velocities
        )

        # Then
        expected_total_est = 10.0 / _MIDDLE_VELOCITY
        self.assertAlmostEqual(expected_total_est, result[0].total_estimated_days, places=1)
        self.assertAlmostEqual(expected_total_est, result[1].total_estimated_days, places=1)

    def test_shouldCalculateDeviationPercentRelativeToEstimatedDays(self):
        # Given
        task = _build_task(
            "TASK-1", "Half-time task",
            story_points=2.0,
            time_by_assignee={"alice": 14400}
        )
        velocities = {"alice": _SENIOR_VELOCITY}

        # When
        result = self.convertor.convert_tasks_to_developers_breakdown(
            [task], ["alice"], velocities
        )

        # Then
        estimated = 2.0 / _SENIOR_VELOCITY
        actual = 1.0
        expected_percent = ((estimated - actual) / estimated) * 100
        self.assertAlmostEqual(expected_percent, result[0].deviation_percent, places=0)


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
        system_metadata=system_metadata,
        assignment=Assignment(),
        time_tracking=time_tracking,
        story_points=story_points
    )
