import unittest
from datetime import datetime

from tasks.app.domain.model.task import TaskSearchCriteria

from velocity.app.domain.calculation.member_group_resolver import MemberGroupResolver
from velocity.app.domain.calculation.velocity_report_calculator import VelocityReportCalculator
from velocity.app.domain.model.velocity import TaskFilter
from velocity.tests.fixtures.velocity_builders import VelocityConfigBuilder
from velocity.tests.mocks.mock_task_repository import MockTaskRepository


class TestApiVelocitySearchCriteria(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.task_repository = MockTaskRepository()
        self.config = VelocityConfigBuilder.sprint_planning_team().build()
        self.member_group_resolver = MemberGroupResolver(self.config)

        self.status_filter = ["Done", "Closed", "Resolved"]
        self.calculator = VelocityReportCalculator(
            task_repository=self.task_repository,
            configuration=self.config,
            member_group_resolver=self.member_group_resolver,
            velocity_search_criteria_factory=lambda: TaskSearchCriteria(
                status_filter=self.status_filter
            )
        )

    async def test_shouldUseResolutionDateRangeWhenIncludeAllStatusesIsFalse(self):
        # Given
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        self.task_repository.mock.search.return_value = []

        # When
        await self.calculator.calculate_velocity_report_for_period(start_date, end_date)

        # Then
        captured_criteria = self.task_repository.mock.search.call_args[0][0]
        self.assertEqual(captured_criteria.resolution_date_range, (start_date, end_date))
        self.assertEqual(captured_criteria.status_filter, self.status_filter)
        self.assertIsNone(captured_criteria.last_modified_date_range)

    async def test_shouldUseLastModifiedDateRangeWhenIncludeAllStatusesIsTrue(self):
        # Given
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        self.task_repository.mock.search.return_value = []

        # When
        await self.calculator.calculate_velocity_report_for_period(
            start_date, end_date, task_filter=TaskFilter(include_all_statuses=True)
        )

        # Then
        captured_criteria = self.task_repository.mock.search.call_args[0][0]
        self.assertEqual(captured_criteria.last_modified_date_range, (start_date, end_date))
        self.assertIsNone(captured_criteria.status_filter)
        self.assertIsNone(captured_criteria.resolution_date_range)

    async def test_shouldClearStatusFilterWhenIncludeAllStatusesIsTrue(self):
        # Given
        start_date = datetime(2024, 3, 1)
        end_date = datetime(2024, 3, 31)
        self.task_repository.mock.search.return_value = []

        # When
        await self.calculator.calculate_velocity_report_for_period(
            start_date, end_date, task_filter=TaskFilter(include_all_statuses=True)
        )

        # Then
        captured_criteria = self.task_repository.mock.search.call_args[0][0]
        self.assertIsNone(captured_criteria.status_filter)

    async def test_shouldApplySameSearchCriteriaForScopedReportsWhenIncludeAllStatuses(self):
        # Given
        start_date = datetime(2024, 2, 1)
        end_date = datetime(2024, 2, 29)
        self.task_repository.mock.search.return_value = []

        # When
        await self.calculator.calculate_scoped_velocity_reports_for_period(
            start_date, end_date, task_filter=TaskFilter(include_all_statuses=True)
        )

        # Then
        captured_criteria = self.task_repository.mock.search.call_args[0][0]
        self.assertEqual(captured_criteria.last_modified_date_range, (start_date, end_date))
        self.assertIsNone(captured_criteria.status_filter)
        self.assertIsNone(captured_criteria.resolution_date_range)

    async def test_shouldApplyCustomQueryWhenProvided(self):
        # Given
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        self.task_repository.mock.search.return_value = []

        custom_query = "[System.Parent] IN (164284, 172447)"

        # When
        await self.calculator.calculate_velocity_report_for_period(
            start_date, end_date, scope_id="headless-team",
            task_filter=TaskFilter(custom_query=custom_query)
        )

        # Then
        captured_criteria = self.task_repository.mock.search.call_args[0][0]
        self.assertEqual(custom_query, captured_criteria.raw_jql_filter)
        self.assertIsNone(captured_criteria.assignee_filter)

    async def test_shouldUseAssigneeFilterWhenNoCustomQueryProvided(self):
        # Given
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        self.task_repository.mock.search.return_value = []

        # When
        await self.calculator.calculate_velocity_report_for_period(
            start_date, end_date, scope_id="development-team"
        )

        # Then
        captured_criteria = self.task_repository.mock.search.call_args[0][0]
        self.assertIsNone(captured_criteria.raw_jql_filter)
        self.assertCountEqual(["alice", "bob", "carol", "dave"], captured_criteria.assignee_filter)
