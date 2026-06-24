import unittest

from ui_web.tests.fixtures.filter_task_builders import task_data
from ui_web.utils.filter_fields import build_field_filters
from ui_web.utils.task_filter_utils import TaskFilterUtils

_FIELD_FILTERS = build_field_filters(["priority", "assignee"])


class TestTaskFilterUtils(unittest.TestCase):

    def test_shouldReturnAllTasksWhenNoSelectionActive(self):
        # given
        tasks = [task_data("TASK-1", priority=1), task_data("TASK-2", priority=2)]

        # when
        result = TaskFilterUtils.filter_tasks(tasks, {}, _FIELD_FILTERS)

        # then
        self.assertEqual(["TASK-1", "TASK-2"], [task.id for task in result])

    def test_shouldKeepOnlyMatchingTasksWhenSingleFieldSelected(self):
        # given
        tasks = [task_data("TASK-1", priority=1), task_data("TASK-2", priority=2), task_data("TASK-3", priority=2)]

        # when
        result = TaskFilterUtils.filter_tasks(tasks, {"priority": "2"}, _FIELD_FILTERS)

        # then
        self.assertEqual(["TASK-2", "TASK-3"], [task.id for task in result])

    def test_shouldApplyLogicalAndAcrossFieldsWhenMultipleSelected(self):
        # given
        tasks = [
            task_data("TASK-1", priority=1, assignee_id="alice"),
            task_data("TASK-2", priority=1, assignee_id="bob"),
            task_data("TASK-3", priority=2, assignee_id="alice"),
        ]

        # when
        result = TaskFilterUtils.filter_tasks(tasks, {"priority": "1", "assignee": "alice"}, _FIELD_FILTERS)

        # then
        self.assertEqual(["TASK-1"], [task.id for task in result])

    def test_shouldReturnEmptyWhenNoTaskMatchesSelection(self):
        # given
        tasks = [task_data("TASK-1", priority=1), task_data("TASK-2", priority=2)]

        # when
        result = TaskFilterUtils.filter_tasks(tasks, {"priority": "9"}, _FIELD_FILTERS)

        # then
        self.assertEqual([], result)
