import unittest

from ui_web.data.task_data import TaskData, AssignmentData, AssigneeData, TimeTrackingData, SystemMetadataData
from ui_web.utils.task_grouping_utils import TaskGroupingUtils


class TestTaskGroupingUtilsGroupByKey(unittest.TestCase):

    def test_shouldGroupTasksByExtractedKeyAndSortAlphabetically(self):
        # Given
        tasks = [
            _build_task("TASK-1", assignee_id="charlie"),
            _build_task("TASK-2", assignee_id="alice"),
            _build_task("TASK-3", assignee_id="alice"),
            _build_task("TASK-4", assignee_id="bob"),
        ]

        # When
        result = TaskGroupingUtils.group_tasks_by_key(
            tasks, key_extractor=lambda t: t.assignment.assignee.id, group_type="developer"
        )

        # Then
        self.assertEqual(3, len(result))
        self.assertEqual("alice", result[0].name)
        self.assertEqual(2, result[0].count)
        self.assertEqual("bob", result[1].name)
        self.assertEqual(1, result[1].count)
        self.assertEqual("charlie", result[2].name)
        self.assertEqual(1, result[2].count)

    def test_shouldExcludeTasksWhereKeyExtractorReturnsNone(self):
        # Given
        tasks = [
            _build_task("TASK-1", assignee_id="alice"),
            _build_task("TASK-2", assignee_id=None),
            _build_task("TASK-3", assignee_id="bob"),
        ]

        # When
        result = TaskGroupingUtils.group_tasks_by_key(
            tasks,
            key_extractor=lambda t: t.assignment.assignee.id if t.assignment.assignee else None,
            group_type="developer"
        )

        # Then
        self.assertEqual(2, len(result))
        group_names = [g.name for g in result]
        self.assertNotIn(None, group_names)

    def test_shouldSetCorrectGroupTypeOnAllGroups(self):
        # Given
        tasks = [
            _build_task("TASK-1", assignee_id="alice"),
            _build_task("TASK-2", assignee_id="bob"),
        ]

        # When
        result = TaskGroupingUtils.group_tasks_by_key(
            tasks, key_extractor=lambda t: t.assignment.assignee.id, group_type="developer"
        )

        # Then
        for group in result:
            self.assertEqual("developer", group.type)


def _build_task(task_id, assignee_id=None):
    assignee = AssigneeData(id=assignee_id, display_name=assignee_id or "") if assignee_id else None
    return TaskData(
        id=task_id,
        title=f"Task {task_id}",
        assignment=AssignmentData(assignee=assignee),
        time_tracking=TimeTrackingData(),
        system_metadata=SystemMetadataData(original_status="To Do")
    )
