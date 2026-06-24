import unittest

from ui_web.convertors.task_filter_convertor import TaskFilterConvertor
from ui_web.tests.fixtures.filter_task_builders import task_data
from ui_web.utils.filter_fields import build_field_filters

_FIELD_FILTERS = build_field_filters(["priority", "assignee"])


class TestTaskFilterConvertorParseSelections(unittest.TestCase):

    def test_shouldReadSelectedValuesForConfiguredFieldsWhenParamsPresent(self):
        # given
        query_params = {"priority": "2", "assignee": "alice"}

        # when
        selections = TaskFilterConvertor.parse_selections(query_params, _FIELD_FILTERS)

        # then
        self.assertEqual({"priority": "2", "assignee": "alice"}, selections)

    def test_shouldIgnoreParamWhenFieldNotConfigured(self):
        # given
        query_params = {"priority": "2", "release": "r1"}

        # when
        selections = TaskFilterConvertor.parse_selections(query_params, _FIELD_FILTERS)

        # then
        self.assertEqual({"priority": "2"}, selections)

    def test_shouldLeaveSelectionsEmptyWhenNoFilterParamsProvided(self):
        # given
        query_params = {"member_group_id": "frontend"}

        # when
        selections = TaskFilterConvertor.parse_selections(query_params, _FIELD_FILTERS)

        # then
        self.assertEqual({}, selections)


class TestTaskFilterConvertorToPanel(unittest.TestCase):

    def test_shouldBuildOneFieldPerConfiguredFieldWhenFieldsHaveOptions(self):
        # given
        tasks = [task_data("TASK-1", priority=1, assignee_id="alice")]

        # when
        panel = TaskFilterConvertor.to_panel(tasks, {}, _FIELD_FILTERS)

        # then
        self.assertEqual(["priority", "assignee"], [field.param for field in panel.fields])

    def test_shouldDropFieldWhenItHasNoOptions(self):
        # given
        tasks = [task_data("TASK-1", priority=None, assignee_id="alice")]
        field_filters = build_field_filters(["priority", "release", "assignee"])

        # when
        panel = TaskFilterConvertor.to_panel(tasks, {}, field_filters)

        # then
        self.assertEqual(["assignee"], [field.param for field in panel.fields])

    def test_shouldMarkSelectedOptionWhenSelectionHasValue(self):
        # given
        tasks = [task_data("TASK-1", priority=1), task_data("TASK-2", priority=2)]

        # when
        panel = TaskFilterConvertor.to_panel(tasks, {"priority": "2"}, _FIELD_FILTERS)

        # then
        priority_field = next(field for field in panel.fields if field.param == "priority")
        self.assertEqual({"2"}, {option.id for option in priority_field.options if option.selected})

    def test_shouldFlagActiveSelectionWhenAnySelectionSet(self):
        # given
        tasks = [task_data("TASK-1", assignee_id="alice")]

        # when
        panel = TaskFilterConvertor.to_panel(tasks, {"assignee": "alice"}, _FIELD_FILTERS)

        # then
        self.assertTrue(panel.has_active_selection)

    def test_shouldNotFlagActiveSelectionWhenSelectionEmpty(self):
        # given
        tasks = [task_data("TASK-1", assignee_id="alice")]

        # when
        panel = TaskFilterConvertor.to_panel(tasks, {}, _FIELD_FILTERS)

        # then
        self.assertFalse(panel.has_active_selection)
