import unittest
from datetime import date

from tasks.app.domain.model.task import MemberGroup
from velocity.app.domain.model.velocity import VelocityReport
from ui_web.convertors.member_convertor import MemberConvertor
from ui_web.convertors.velocity_chart_convertor import VelocityChartConvertor
from ui_web.convertors.velocity_report_convertor import VelocityReportConvertor
from ui_web.facades.team_velocity_facade import TeamVelocityFacade
from ui_web.tests.mocks.mock_velocity_api import MockVelocityApi
from ui_web.tests.mocks.mock_assignee_search_api import MockAssigneeSearchApi

_CUSTOM_FILTERS = {"backend-team": "parent in (PROJ-100, PROJ-200)"}

_AVAILABLE_MEMBER_GROUPS = [
    MemberGroup(id="backend-team", name="Backend Team"),
    MemberGroup(id="frontend-team", name="Frontend Team"),
]


def _create_facade(velocity_api, assignee_search_api,
                   member_group_custom_filters=None):
    return TeamVelocityFacade(
        velocity_api=velocity_api,
        assignee_search_api=assignee_search_api,
        available_member_groups=_AVAILABLE_MEMBER_GROUPS,
        member_convertor=MemberConvertor(),
        velocity_chart_convertor=VelocityChartConvertor(),
        velocity_report_convertor=VelocityReportConvertor(assignee_search_api),
        member_group_custom_filters=member_group_custom_filters
    )


def _build_velocity_report(start_date, velocity, story_points,
                            scope=None, scope_name=None):
    return VelocityReport(
        start_date=start_date,
        end_date=date(start_date.year, start_date.month, 28),
        velocity=velocity,
        story_points=story_points,
        metric_scope=scope,
        metric_scope_name=scope_name
    )


class TestTeamVelocityFacadeCustomFilter(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.velocity_api = MockVelocityApi()
        self.assignee_search_api = MockAssigneeSearchApi()

    def test_shouldDetectCustomFilterWhenMemberGroupHasConfiguredFilter(self):
        # Given
        facade = _create_facade(self.velocity_api, self.assignee_search_api,
                                member_group_custom_filters=_CUSTOM_FILTERS)

        # When
        result = facade.has_custom_filter("backend-team")

        # Then
        self.assertTrue(result)

    def test_shouldNotDetectCustomFilterWhenMemberGroupHasNoConfiguration(self):
        # Given
        facade = _create_facade(self.velocity_api, self.assignee_search_api,
                                member_group_custom_filters=_CUSTOM_FILTERS)

        # When
        result = facade.has_custom_filter("frontend-team")

        # Then
        self.assertFalse(result)

    def test_shouldNotDetectCustomFilterWhenNoMemberGroupSpecified(self):
        # Given
        facade = _create_facade(self.velocity_api, self.assignee_search_api,
                                member_group_custom_filters=_CUSTOM_FILTERS)

        # When
        result = facade.has_custom_filter(None)

        # Then
        self.assertFalse(result)

    async def test_shouldPassCustomQueryToVelocityApiWhenCustomFilterEnabled(self):
        # Given
        self.velocity_api.mock.generate_velocity_report.return_value = []
        facade = _create_facade(self.velocity_api, self.assignee_search_api,
                                member_group_custom_filters=_CUSTOM_FILTERS)

        # When
        await facade.get_velocity_reports_data(
            member_group_id="backend-team", use_custom_filter=True
        )

        # Then
        parameters = self.velocity_api.mock.generate_velocity_report.call_args[0][0]
        self.assertEqual("parent in (PROJ-100, PROJ-200)", parameters.task_filter.custom_query)

    async def test_shouldNotPassCustomQueryWhenCustomFilterDisabled(self):
        # Given
        self.velocity_api.mock.generate_velocity_report.return_value = []
        facade = _create_facade(self.velocity_api, self.assignee_search_api,
                                member_group_custom_filters=_CUSTOM_FILTERS)

        # When
        await facade.get_velocity_reports_data(
            member_group_id="backend-team", use_custom_filter=False
        )

        # Then
        parameters = self.velocity_api.mock.generate_velocity_report.call_args[0][0]
        self.assertIsNone(parameters.task_filter.custom_query)


if __name__ == '__main__':
    unittest.main()
