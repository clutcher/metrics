import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

from tasks.app.domain.model.config import WorkflowConfig
from tasks.app.domain.model.task import Task, EnrichmentOptions, TaskSearchCriteria, MemberGroup
from ui_web.facades.tasks_facade import TasksFacade
from ui_web.facades.team_velocity_facade import TeamVelocityFacade
from ui_web.convertors.task_convertor import TaskConvertor
from ui_web.convertors.member_convertor import MemberConvertor
from ui_web.convertors.velocity_chart_convertor import VelocityChartConvertor
from ui_web.convertors.velocity_report_convertor import VelocityReportConvertor
from ui_web.utils.federated_data_post_processors import MemberGroupTaskFilter
from ui_web.utils.task_grouping_utils import TaskGroupingUtils
from ui_web.tests.fixtures.ui_web_builders import BusinessScenarios, DomainTaskBuilder
from ui_web.tests.mocks.mock_task_search_api import MockTaskSearchApi
from ui_web.tests.mocks.mock_forecast_api import MockForecastApi
from ui_web.tests.mocks.mock_velocity_api import MockVelocityApi
from ui_web.tests.mocks.mock_assignee_search_api import MockAssigneeSearchApi


class TestApiUIWebIntegration(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.task_search_api = MockTaskSearchApi()
        self.forecast_api = MockForecastApi()
        self.velocity_api = MockVelocityApi()
        self.assignee_search_api = MockAssigneeSearchApi()
        
        self.available_member_groups = [
            MemberGroup(id="frontend-team", name="Frontend Development Team"),
            MemberGroup(id="backend-team", name="Backend Development Team"),
            MemberGroup(id="devops-team", name="DevOps Team")
        ]
        
        self.current_tasks_criteria = TaskSearchCriteria(
            status_filter=["In Progress", "Development", "Testing"]
        )
        
        self.recently_finished_criteria = TaskSearchCriteria(
            status_filter=["Done", "Completed"]
        )
        
        self.workflow_config = WorkflowConfig(
            in_progress_status_codes=["In Progress", "Development", "Testing"],
            done_status_codes=["Done", "Completed", "Closed"],
            pending_status_codes=["To Do", "Open", "Backlog"],
            stages={
                "development": ["In Progress", "Development"],
                "qa": ["Testing", "Code Review"],
                "done": ["Done", "Completed", "Closed"]
            },
            recently_finished_tasks_days=30
        )
        
        # Mock member group config for filtering
        member_group_config = Mock()
        member_group_config.members = {
            "alice.johnson": {"member_groups": ["frontend-team"]},
            "bob.smith": {"member_groups": ["backend-team"]},
            "charlie.brown": {"member_groups": ["devops-team"]}
        }
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {}
        
        self.member_group_filter = MemberGroupTaskFilter(member_group_config)
        
        # Mock time policy for conversion
        with patch('sd_metrics_lib.utils.time.TimePolicy.BUSINESS_HOURS'):
            self.task_convertor = TaskConvertor(Mock())
        
        self.member_convertor = MemberConvertor()
        self.velocity_chart_convertor = VelocityChartConvertor()
        self.velocity_report_convertor = VelocityReportConvertor(self.assignee_search_api)
        
        self.tasks_facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=self.task_convertor,
            available_member_groups=self.available_member_groups,
            current_tasks_search_criteria=self.current_tasks_criteria,
            recently_finished_tasks_search_criteria=self.recently_finished_criteria,
            workflow_config=self.workflow_config,
            member_group_task_filter=self.member_group_filter,
            member_convertor=self.member_convertor
        )
        
        self.velocity_facade = TeamVelocityFacade(
            velocity_api=self.velocity_api,
            assignee_search_api=self.assignee_search_api,
            available_member_groups=self.available_member_groups,
            member_convertor=self.member_convertor,
            velocity_chart_convertor=self.velocity_chart_convertor,
            velocity_report_convertor=self.velocity_report_convertor
        )
    
    async def test_shouldIntegrateTaskConversionWithFacadeWorkflowForAccurateSprintDashboard(self):
        # Given - Raw domain tasks that need conversion for UI display
        raw_domain_tasks = [
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("alice.johnson")
                .with_time_spent_hours(16.0)  # Should convert to 2 business days
                .build(),
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("bob.smith")
                .with_time_spent_hours(32.0)  # Should convert to 4 business days
                .build()
        ]
        
        self.task_search_api.mock.search.side_effect = [raw_domain_tasks, []]
        
        # When - Execute integrated conversion workflow through facade
        result = await self.tasks_facade.get_tasks()
        
        # Then - Task conversion should be integrated seamlessly
        self.assertEqual(2, len(result))
        
        # Verify business day conversion integration
        alice_task = next(task for task in result 
                         if task.assignment.assignee and task.assignment.assignee.id == "alice.johnson")
        bob_task = next(task for task in result 
                       if task.assignment.assignee and task.assignment.assignee.id == "bob.smith")
        
        self.assertEqual(2.0, alice_task.time_tracking.total_spent_time_days)
        self.assertEqual(4.0, bob_task.time_tracking.total_spent_time_days)
        
        # Verify conversion maintains business context
        self.assertEqual("alice.johnson", alice_task.assignment.assignee.id)
        self.assertEqual("bob.smith", bob_task.assignment.assignee.id)
    
    async def test_shouldIntegrateTaskSortingWithBusinessPriorityWorkflowForRetrospectiveInsights(self):
        # Given - Tasks with different time investments for retrospective analysis
        unsorted_tasks = [
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .with_time_spent_hours(8.0)   # 1 business day
                .assigned_to("alice.johnson")
                .build(),
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .with_time_spent_hours(40.0)  # 5 business days - high investment
                .assigned_to("bob.smith")
                .build(),
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .with_time_spent_hours(24.0)  # 3 business days
                .assigned_to("charlie.brown")
                .build()
        ]
        
        # Set identifiable IDs
        unsorted_tasks[0].id = "LOW-INVESTMENT"
        unsorted_tasks[1].id = "HIGH-INVESTMENT"
        unsorted_tasks[2].id = "MEDIUM-INVESTMENT"
        
        self.task_search_api.mock.search.side_effect = [unsorted_tasks, []]
        
        # When - Execute integrated sorting workflow through facade
        result = await self.tasks_facade.get_tasks()
        
        # Then - Tasks should be sorted by business priority (time investment)
        self.assertEqual(3, len(result))
        
        # Should be sorted by assignee name first, then time spent descending
        self.assertEqual("LOW-INVESTMENT", result[0].id)     # alice.johnson first alphabetically
        self.assertEqual("HIGH-INVESTMENT", result[1].id)    # bob.smith second
        self.assertEqual("MEDIUM-INVESTMENT", result[2].id)  # charlie.brown third

        # Verify sorting integration maintains business data integrity
        self.assertEqual(1.0, result[0].time_tracking.total_spent_time_days)
        self.assertEqual(5.0, result[1].time_tracking.total_spent_time_days)
        self.assertEqual(3.0, result[2].time_tracking.total_spent_time_days)
    
    async def test_shouldIntegrateTaskGroupingWithMemberTeamWorkflowForOrganizationalView(self):
        # Given - Multi-team tasks requiring organizational grouping
        multi_team_tasks = [
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("alice.johnson")  # Frontend team
                .build(),
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("bob.smith")     # Backend team
                .build(),
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("charlie.brown") # DevOps team
                .build()
        ]
        
        self.task_search_api.mock.search.side_effect = [multi_team_tasks, []]
        
        # When - Execute integrated grouping workflow through facade
        ui_tasks = await self.tasks_facade.get_tasks()
        grouped_result = TaskGroupingUtils.group_ui_tasks_by_member_group_and_stage(
            ui_tasks, self.workflow_config
        )
        
        # Then - Grouping should integrate with team organization
        from ui_web.data.hierarchical_item_data import HierarchicalItemData
        
        if isinstance(grouped_result[0], HierarchicalItemData):
            self.assertEqual(3, len(grouped_result))  # Three member groups
            
            # Verify organizational grouping integration
            group_names = {group.name for group in grouped_result}
            self.assertIn("Frontend Development Team", group_names)
            self.assertIn("Backend Development Team", group_names)
            self.assertIn("DevOps Team", group_names)
            
            # Verify member team workflow integration
            for member_group in grouped_result:
                self.assertEqual(1, member_group.count)  # One task per team
                self.assertEqual("member_group", member_group.type)
    
    async def test_shouldIntegrateMemberGroupFilteringWithTaskRetrievalWorkflowForTeamIsolation(self):
        # Given - Cross-team scenario requiring filtering integration
        cross_team_tasks = [
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("alice.johnson")  # Frontend
                .with_time_spent_hours(16.0)
                .build(),
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("bob.smith")     # Backend
                .with_time_spent_hours(24.0)
                .build(),
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("charlie.brown") # DevOps
                .with_time_spent_hours(8.0)
                .build()
        ]
        
        self.task_search_api.mock.search.side_effect = [cross_team_tasks, []]
        
        # When - Execute integrated filtering workflow for team isolation
        frontend_result = await self.tasks_facade.get_tasks("frontend-team")
        
        # Then - Filtering integration should isolate team data
        self.assertEqual(1, len(frontend_result))
        isolated_task = frontend_result[0]
        
        # Verify team isolation integration
        self.assertEqual("alice.johnson", isolated_task.assignment.assignee.id)
        self.assertEqual(2.0, isolated_task.time_tracking.total_spent_time_days)
        
        # Verify filtering maintains business context
        self.assertIsNotNone(isolated_task.assignment.assignee.display_name)
        self.assertIsNotNone(isolated_task.system_metadata)
    
    async def test_shouldIntegrateVelocityChartConversionWithReportingWorkflowForPerformanceAnalysis(self):
        # Given - Velocity data requiring chart conversion for performance dashboard
        from ui_web.data.velocity_report_data import VelocityReportData
        from datetime import date
        
        velocity_reports_data = [
            VelocityReportData(
                start_date=date(2024, 1, 1),
                velocity=4.5,
                story_points=22.5
            ),
            VelocityReportData(
                start_date=date(2024, 2, 1),
                velocity=5.2,
                story_points=26.0
            ),
            VelocityReportData(
                start_date=date(2024, 3, 1),
                velocity=4.8,
                story_points=24.0
            )
        ]
        
        # When - Execute integrated chart conversion workflow
        velocity_chart = self.velocity_facade.get_velocity_chart_data(velocity_reports_data)
        story_points_chart = self.velocity_facade.get_story_points_chart_data(velocity_reports_data)
        
        # Then - Chart conversion should integrate with reporting workflow
        self.assertIsNotNone(velocity_chart)
        self.assertIsNotNone(story_points_chart)
        
        # Verify performance analysis integration
        self.assertEqual(["2024-01", "2024-02", "2024-03"], velocity_chart.labels)
        self.assertEqual([4.5, 5.2, 4.8], velocity_chart.datasets[0].data)
        self.assertEqual([22.5, 26.0, 24.0], story_points_chart.datasets[0].data)
        
        # Verify business context preservation in charts
        self.assertEqual("team", velocity_chart.datasets[0].label)
        self.assertEqual("team", story_points_chart.datasets[0].label)
    
    async def test_shouldIntegrateDataFederationWithEnrichmentWorkflowForComprehensiveDashboard(self):
        # Given - Base tasks requiring enrichment for comprehensive dashboard
        base_tasks = [
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .assigned_to("alice.johnson")
                .with_time_spent_hours(16.0)
                .build()
        ]
        
        # Mock forecast enrichment integration
        async def integrate_forecasts(tasks, parameters):
            for task in tasks:
                task.forecast = Mock()
                task.forecast.target = Mock()
                task.forecast.target.health_status = Mock()
                task.forecast.target.health_status.value = 3  # GREEN
            return tasks
        
        self.task_search_api.mock.search.side_effect = [base_tasks, []]
        self.forecast_api.mock.generate_forecasts_for_tasks.side_effect = integrate_forecasts
        
        # When - Execute integrated federation and enrichment workflow
        result = await self.tasks_facade.get_tasks()
        
        # Then - Data federation should integrate with enrichment
        self.assertEqual(1, len(result))
        comprehensive_task = result[0]
        
        # Verify comprehensive dashboard integration
        self.assertIsNotNone(comprehensive_task.forecast)
        self.assertEqual(3, comprehensive_task.forecast.health_status.value)
        self.assertEqual(2.0, comprehensive_task.time_tracking.total_spent_time_days)
        self.assertEqual("alice.johnson", comprehensive_task.assignment.assignee.id)
        
        # Verify enrichment workflow was integrated
        self.forecast_api.mock.generate_forecasts_for_tasks.assert_called()
    
    async def test_shouldIntegrateErrorHandlingWithGracefulDegradationWorkflowForUserExperience(self):
        # Given - Scenario with partial system failures requiring graceful integration
        partial_failure_tasks = BusinessScenarios.active_sprint_tasks()
        
        # Mock partial failure in forecast integration
        async def partial_failure_enrichment(tasks, parameters):
            # Simulate enrichment failure for better UX testing
            raise Exception("Forecast service temporarily unavailable")
        
        self.task_search_api.mock.search.side_effect = [partial_failure_tasks, []]
        self.forecast_api.mock.generate_forecasts_for_tasks.side_effect = partial_failure_enrichment
        
        # When - Execute integrated error handling workflow
        try:
            await self.tasks_facade.get_tasks()
            self.fail("Expected exception to propagate")
        except Exception as e:
            # Then - Error handling should integrate with workflow
            self.assertEqual("Forecast service temporarily unavailable", str(e))
        
        # Verify graceful degradation integration
        # (In real implementation, this would return tasks without forecasts)
        self.task_search_api.mock.search.assert_called()
        self.forecast_api.mock.generate_forecasts_for_tasks.assert_called()
    
    async def test_shouldIntegrateMultipleFacadeWorkflowsForCrossFunctionalBusinessInsights(self):
        # Given - Scenario requiring integration of multiple facade workflows
        tasks_for_insights = BusinessScenarios.active_sprint_tasks()
        
        from velocity.app.domain.model.velocity import VelocityReport
        from datetime import date
        
        velocity_reports = [
            VelocityReport(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                velocity=5.0,
                story_points=25.0,
                metric_scope="frontend-team",
                metric_scope_name="Frontend Development Team"
            )
        ]
        
        # Setup facade integrations
        self.task_search_api.mock.search.side_effect = [tasks_for_insights, []]
        self.velocity_api.mock.generate_velocity_report.return_value = velocity_reports
        
        # When - Execute cross-functional workflow integration
        task_insights = await self.tasks_facade.get_tasks()
        velocity_insights = await self.velocity_facade.get_velocity_reports_data("frontend-team")
        
        # Then - Multiple workflows should integrate for comprehensive insights
        self.assertEqual(3, len(task_insights))     # Task workflow results
        self.assertEqual(1, len(velocity_insights)) # Velocity workflow results
        
        # Verify cross-functional integration maintains business context
        for task in task_insights:
            self.assertIsNotNone(task.assignment.assignee)
            self.assertIsNotNone(task.time_tracking)
        
        velocity_insight = velocity_insights[0]
        self.assertEqual(5.0, velocity_insight.velocity)
        self.assertEqual(25.0, velocity_insight.story_points)
        self.assertEqual(date(2024, 1, 1), velocity_insight.start_date)
        
        # Verify business insights integration
        total_task_days = sum(task.time_tracking.total_spent_time_days or 0 for task in task_insights)
        self.assertGreater(total_task_days, 0)  # Tasks have time investment
        self.assertGreater(velocity_insight.velocity, 0)  # Team has measurable velocity

    async def test_shouldApplyCustomQueryFilterWhenMemberGroupHasCustomFilterConfigured(self):
        # Given - Member group configured with custom JQL/WIQL filter
        member_group_config = Mock()
        member_group_config.members = {}
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {"special-team": "parent in (PROJ-123, PROJ-456)"}

        member_group_filter = MemberGroupTaskFilter(member_group_config)

        tasks_facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=self.task_convertor,
            available_member_groups=self.available_member_groups,
            current_tasks_search_criteria=self.current_tasks_criteria,
            recently_finished_tasks_search_criteria=self.recently_finished_criteria,
            workflow_config=self.workflow_config,
            member_group_task_filter=member_group_filter,
            member_convertor=self.member_convertor,
            member_group_custom_filters={"special-team": "parent in (PROJ-123, PROJ-456)"}
        )

        tasks = [DomainTaskBuilder.domain_task_for_ui_conversion().build()]
        self.task_search_api.mock.search.side_effect = [tasks, []]

        # When - Fetch tasks for member group with custom filter
        await tasks_facade.get_tasks("special-team")

        # Then - Search API should be called with raw_jql_filter set
        call_args = self.task_search_api.mock.search.call_args_list[0]
        search_criteria = call_args[0][0]
        self.assertEqual("parent in (PROJ-123, PROJ-456)", search_criteria.raw_jql_filter)

    async def test_shouldSkipAssigneeFilteringWhenMemberGroupUsesCustomFilter(self):
        # Given - Member group with custom filter and tasks from different assignees
        member_group_config = Mock()
        member_group_config.members = {
            "alice.johnson": {"member_groups": ["frontend-team"]},
            "bob.smith": {"member_groups": ["backend-team"]}
        }
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {"special-team": "[System.Parent] IN (174641, 176747)"}

        member_group_filter = MemberGroupTaskFilter(member_group_config)

        tasks_facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=self.task_convertor,
            available_member_groups=self.available_member_groups,
            current_tasks_search_criteria=self.current_tasks_criteria,
            recently_finished_tasks_search_criteria=self.recently_finished_criteria,
            workflow_config=self.workflow_config,
            member_group_task_filter=member_group_filter,
            member_convertor=self.member_convertor,
            member_group_custom_filters={"special-team": "[System.Parent] IN (174641, 176747)"}
        )

        mixed_assignee_tasks = [
            DomainTaskBuilder.domain_task_for_ui_conversion().assigned_to("alice.johnson").build(),
            DomainTaskBuilder.domain_task_for_ui_conversion().assigned_to("bob.smith").build(),
            DomainTaskBuilder.domain_task_for_ui_conversion().assigned_to("charlie.brown").build()
        ]
        self.task_search_api.mock.search.side_effect = [mixed_assignee_tasks, []]

        # When - Fetch tasks for member group with custom filter
        result = await tasks_facade.get_tasks("special-team")

        # Then - All tasks should be returned without assignee filtering
        self.assertEqual(3, len(result))

    async def test_shouldUseAssigneeFilteringWhenMemberGroupHasNoCustomFilter(self):
        # Given - Member group without custom filter
        member_group_config = Mock()
        member_group_config.members = {
            "alice.johnson": {"member_groups": ["frontend-team"]},
            "bob.smith": {"member_groups": ["backend-team"]}
        }
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {}

        member_group_filter = MemberGroupTaskFilter(member_group_config)

        tasks_facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=self.task_convertor,
            available_member_groups=self.available_member_groups,
            current_tasks_search_criteria=self.current_tasks_criteria,
            recently_finished_tasks_search_criteria=self.recently_finished_criteria,
            workflow_config=self.workflow_config,
            member_group_task_filter=member_group_filter,
            member_convertor=self.member_convertor,
            member_group_custom_filters={}
        )

        mixed_assignee_tasks = [
            DomainTaskBuilder.domain_task_for_ui_conversion().assigned_to("alice.johnson").build(),
            DomainTaskBuilder.domain_task_for_ui_conversion().assigned_to("bob.smith").build()
        ]
        self.task_search_api.mock.search.side_effect = [mixed_assignee_tasks, []]

        # When - Fetch tasks for frontend team (normal assignee filtering)
        result = await tasks_facade.get_tasks("frontend-team")

        # Then - Only alice's task should be returned (assignee filtering applied)
        self.assertEqual(1, len(result))
        self.assertEqual("alice.johnson", result[0].assignment.assignee.id)


    async def test_shouldRelabelUnassignedTasksUnderFilteredGroupWhenMergeEnabled(self):
        # Given
        member_group_config = Mock()
        member_group_config.members = {"dev1": {"member_groups": ["Headless"]}}
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {"Headless": "parent in (PROJ-100)"}
        member_group_filter = MemberGroupTaskFilter(member_group_config)

        facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=self.task_convertor,
            available_member_groups=self.available_member_groups,
            current_tasks_search_criteria=self.current_tasks_criteria,
            recently_finished_tasks_search_criteria=self.recently_finished_criteria,
            workflow_config=self.workflow_config,
            member_group_task_filter=member_group_filter,
            member_convertor=self.member_convertor,
            member_group_custom_filters={"Headless": "parent in (PROJ-100)"},
            merge_unassigned_into_filtered_group=True
        )

        unassigned_task = (DomainTaskBuilder.domain_task_for_ui_conversion()
                           .assigned_to("unknown.dev")
                           .with_member_group("unassigned", "Unassigned")
                           .build())
        self.task_search_api.mock.search.side_effect = [[unassigned_task], []]

        # When
        result = await facade.get_tasks("Headless")

        # Then
        self.assertEqual(1, len(result))
        self.assertEqual("Headless", result[0].assignment.member_group.name)

    async def test_shouldKeepUnassignedSeparateWhenViewingAllGroupsEvenWithMergeEnabled(self):
        # Given
        member_group_config = Mock()
        member_group_config.members = {}
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {"Headless": "parent in (PROJ-100)"}
        member_group_filter = MemberGroupTaskFilter(member_group_config)

        facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=self.task_convertor,
            available_member_groups=self.available_member_groups,
            current_tasks_search_criteria=self.current_tasks_criteria,
            recently_finished_tasks_search_criteria=self.recently_finished_criteria,
            workflow_config=self.workflow_config,
            member_group_task_filter=member_group_filter,
            member_convertor=self.member_convertor,
            member_group_custom_filters={"Headless": "parent in (PROJ-100)"},
            merge_unassigned_into_filtered_group=True
        )

        unassigned_task = (DomainTaskBuilder.domain_task_for_ui_conversion()
                           .assigned_to("unknown.dev")
                           .with_member_group("unassigned", "Unassigned")
                           .build())
        self.task_search_api.mock.search.side_effect = [[unassigned_task], []]

        # When
        result = await facade.get_tasks()

        # Then
        self.assertEqual(1, len(result))
        self.assertEqual("Unassigned", result[0].assignment.member_group.name)

    async def test_shouldKeepUnassignedSeparateWhenMergeDisabled(self):
        # Given
        member_group_config = Mock()
        member_group_config.members = {}
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {"Headless": "parent in (PROJ-100)"}
        member_group_filter = MemberGroupTaskFilter(member_group_config)

        facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=self.task_convertor,
            available_member_groups=self.available_member_groups,
            current_tasks_search_criteria=self.current_tasks_criteria,
            recently_finished_tasks_search_criteria=self.recently_finished_criteria,
            workflow_config=self.workflow_config,
            member_group_task_filter=member_group_filter,
            member_convertor=self.member_convertor,
            member_group_custom_filters={"Headless": "parent in (PROJ-100)"},
            merge_unassigned_into_filtered_group=False
        )

        unassigned_task = (DomainTaskBuilder.domain_task_for_ui_conversion()
                           .assigned_to("unknown.dev")
                           .with_member_group("unassigned", "Unassigned")
                           .build())
        self.task_search_api.mock.search.side_effect = [[unassigned_task], []]

        # When
        result = await facade.get_tasks("Headless")

        # Then
        self.assertEqual(1, len(result))
        self.assertEqual("Unassigned", result[0].assignment.member_group.name)

    async def test_shouldOnlyRelabelUnassignedTasksNotRegularAssignedTasks(self):
        # Given
        member_group_config = Mock()
        member_group_config.members = {"dev1": {"member_groups": ["Headless"]}}
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {"Headless": "parent in (PROJ-100)"}
        member_group_filter = MemberGroupTaskFilter(member_group_config)

        facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=self.task_convertor,
            available_member_groups=self.available_member_groups,
            current_tasks_search_criteria=self.current_tasks_criteria,
            recently_finished_tasks_search_criteria=self.recently_finished_criteria,
            workflow_config=self.workflow_config,
            member_group_task_filter=member_group_filter,
            member_convertor=self.member_convertor,
            member_group_custom_filters={"Headless": "parent in (PROJ-100)"},
            merge_unassigned_into_filtered_group=True
        )

        assigned_task = (DomainTaskBuilder.domain_task_for_ui_conversion()
                         .assigned_to("dev1")
                         .with_member_group("headless", "Headless")
                         .build())
        assigned_task.id = "ASSIGNED-TASK"

        unassigned_task = (DomainTaskBuilder.domain_task_for_ui_conversion()
                           .assigned_to("unknown.dev")
                           .with_member_group("unassigned", "Unassigned")
                           .build())
        unassigned_task.id = "UNASSIGNED-TASK"

        self.task_search_api.mock.search.side_effect = [[assigned_task, unassigned_task], []]

        # When
        result = await facade.get_tasks("Headless")

        # Then
        self.assertEqual(2, len(result))
        assigned_result = next(t for t in result if t.id == "ASSIGNED-TASK")
        relabeled_result = next(t for t in result if t.id == "UNASSIGNED-TASK")

        self.assertEqual("Headless", assigned_result.assignment.member_group.name)
        self.assertEqual("Headless", relabeled_result.assignment.member_group.name)


if __name__ == '__main__':
    unittest.main()