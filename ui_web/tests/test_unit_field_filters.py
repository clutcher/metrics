import unittest

from sd_metrics_lib.utils.enums import HealthStatus

from ui_web.data.task_filter_data import NO_PARENT_OPTION_ID, UNASSIGNED_OPTION_ID
from ui_web.tests.fixtures.filter_task_builders import task_data
from ui_web.utils.filter_fields import build_field_filters


def _field_filter(field_name):
    return build_field_filters([field_name])[0]


class TestPriorityFilter(unittest.TestCase):

    def test_shouldOfferDistinctPrioritiesAscendingWhenTasksHavePriorities(self):
        # given
        tasks = [task_data("TASK-1", priority=3), task_data("TASK-2", priority=1), task_data("TASK-3", priority=1)]

        # when
        field = _field_filter("priority").to_field(tasks, None)

        # then
        self.assertEqual(["Priority 1", "Priority 3"], [option.label for option in field.options])

    def test_shouldMatchTaskWhenPriorityEqualsSelectedValue(self):
        # given
        task = task_data("TASK-1", priority=2)

        # when
        result = _field_filter("priority").matches(task, "2")

        # then
        self.assertTrue(result)


class TestReleaseFilter(unittest.TestCase):

    def test_shouldOfferDistinctReleasesSortedByNaturalNameWhenTasksHaveReleases(self):
        # given
        tasks = [task_data("TASK-1", releases=[("r2", "Sprint 10")]), task_data("TASK-2", releases=[("r1", "Sprint 2")])]

        # when
        field = _field_filter("release").to_field(tasks, None)

        # then
        self.assertEqual(["Sprint 2", "Sprint 10"], [option.label for option in field.options])

    def test_shouldMatchTaskWhenAnyReleaseEqualsSelectedValue(self):
        # given
        task = task_data("TASK-1", releases=[("r1", "Sprint 2"), ("r2", "Sprint 10")])

        # when
        result = _field_filter("release").matches(task, "r2")

        # then
        self.assertTrue(result)


class TestAssigneeFilter(unittest.TestCase):

    def test_shouldPrependUnassignedOptionWhenSomeTasksHaveNoAssignee(self):
        # given
        tasks = [task_data("TASK-1", assignee_id="alice"), task_data("TASK-2", assignee_id=None)]

        # when
        field = _field_filter("assignee").to_field(tasks, None)

        # then
        self.assertEqual(UNASSIGNED_OPTION_ID, field.options[0].id)

    def test_shouldMatchUnassignedTasksWhenUnassignedSentinelSelected(self):
        # given
        task = task_data("TASK-1", assignee_id=None)

        # when
        result = _field_filter("assignee").matches(task, UNASSIGNED_OPTION_ID)

        # then
        self.assertTrue(result)

    def test_shouldMarkChosenOptionAsSelectedWhenItMatchesCriteriaValue(self):
        # given
        tasks = [task_data("TASK-1", assignee_id="alice"), task_data("TASK-2", assignee_id="bob")]

        # when
        field = _field_filter("assignee").to_field(tasks, "bob")

        # then
        self.assertEqual({"bob"}, {option.id for option in field.options if option.selected})


class TestParentFilter(unittest.TestCase):

    def test_shouldLabelParentByIdWhenParentTitleMissing(self):
        # given
        tasks = [task_data("TASK-1", parent_id="EPIC-7", parent_title="")]

        # when
        field = _field_filter("parent").to_field(tasks, None)

        # then
        self.assertEqual("EPIC-7", field.options[0].label)

    def test_shouldMatchTasksWithoutParentWhenNoParentSentinelSelected(self):
        # given
        task = task_data("TASK-1", parent_id=None)

        # when
        result = _field_filter("parent").matches(task, NO_PARENT_OPTION_ID)

        # then
        self.assertTrue(result)


class TestStoryPointsFilter(unittest.TestCase):

    def test_shouldFormatIntegerStoryPointsWithoutDecimalWhenWholeNumber(self):
        # given
        tasks = [task_data("TASK-1", story_points=3.0)]

        # when
        field = _field_filter("story_points").to_field(tasks, None)

        # then
        self.assertEqual("3", field.options[0].label)


class TestStageFilter(unittest.TestCase):

    def test_shouldReturnNoFieldWhenNoTaskHasStage(self):
        # given
        tasks = [task_data("TASK-1", stage=None)]

        # when
        field = _field_filter("stage").to_field(tasks, None)

        # then
        self.assertIsNone(field)


class TestHealthFilter(unittest.TestCase):

    def test_shouldOfferAllHealthStatusesAsFixedOptionsEvenWhenTasksHaveNoForecast(self):
        # given
        tasks = [task_data("TASK-1", health=None)]

        # when
        field = _field_filter("health").to_field(tasks, None)

        # then
        self.assertEqual([status.name for status in HealthStatus], [option.id for option in field.options])

    def test_shouldMatchTaskWhenHealthStatusEqualsSelectedValue(self):
        # given
        task = task_data("TASK-1", health=HealthStatus.RED)

        # when
        result = _field_filter("health").matches(task, "RED")

        # then
        self.assertTrue(result)

    def test_shouldFlagRequiresEnrichmentWhenFilterIsHealth(self):
        # given
        field_filter = _field_filter("health")

        # when
        requires_enrichment = field_filter.requires_enrichment

        # then
        self.assertTrue(requires_enrichment)


class TestBuildFieldFilters(unittest.TestCase):

    def test_shouldBuildFieldFiltersInConfiguredOrderWhenNamesKnown(self):
        # given
        field_names = ["stage", "priority", "health"]

        # when
        field_filters = build_field_filters(field_names)

        # then
        self.assertEqual(["stage", "priority", "health"], [field_filter.param for field_filter in field_filters])

    def test_shouldSkipUnknownNamesWhenBuildingFieldFilters(self):
        # given
        field_names = ["priority", "made_up_field", "assignee"]

        # when
        field_filters = build_field_filters(field_names)

        # then
        self.assertEqual(["priority", "assignee"], [field_filter.param for field_filter in field_filters])
