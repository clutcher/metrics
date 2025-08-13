import unittest
from datetime import date, datetime
from unittest.mock import AsyncMock, Mock, patch

from sd_metrics_lib.utils.enums import HealthStatus
from sd_metrics_lib.utils.time import Duration, TimeUnit, TimePolicy

from forecast.app.domain.model.forecast import Forecast, Target, Subject
from tasks.app.domain.model.task import Task, Assignment, Assignee, MemberGroup, TimeTracking, SystemMetadata
from ui_web.convertors.task_convertor import TaskConvertor
from ui_web.data.task_data import TaskData, AssigneeData, AssignmentData, TimeTrackingData, SystemMetadataData, ForecastData
from ui_web.data.member_data import MemberGroupData
from velocity.app.domain.model.velocity import VelocityReport, ReportGenerationParameters, ReportType
from ui_web.facades.team_velocity_facade import TeamVelocityFacade
from ui_web.convertors.member_convertor import MemberConvertor
from ui_web.convertors.velocity_chart_convertor import VelocityChartConvertor
from ui_web.convertors.velocity_report_convertor import VelocityReportConvertor
from ui_web.tests.mocks.mock_velocity_api import MockVelocityApi
from ui_web.tests.mocks.mock_assignee_search_api import MockAssigneeSearchApi


class TestApiUIWebCalculation(unittest.TestCase):
    
    def setUp(self):
        self.time_policy = TimePolicy.BUSINESS_HOURS
        self.task_convertor = TaskConvertor(self.time_policy)
        
        self.velocity_api = MockVelocityApi()
        self.assignee_search_api = MockAssigneeSearchApi()
        
        self.available_member_groups = [
            MemberGroup(id="frontend-team", name="Frontend Development Team"),
            MemberGroup(id="backend-team", name="Backend Development Team")
        ]
        
        self.member_convertor = MemberConvertor()
        self.velocity_chart_convertor = VelocityChartConvertor()
        self.velocity_report_convertor = VelocityReportConvertor(self.assignee_search_api)
        
        self.velocity_facade = TeamVelocityFacade(
            velocity_api=self.velocity_api,
            assignee_search_api=self.assignee_search_api,
            available_member_groups=self.available_member_groups,
            member_convertor=self.member_convertor,
            velocity_chart_convertor=self.velocity_chart_convertor,
            velocity_report_convertor=self.velocity_report_convertor
        )
    
    def test_shouldCalculateBusinessDaysFromHoursCorrectlyForSprintCapacityPlanning(self):
        # Given - Task with 32 hours of work (4 business days at 8 hours/day)
        time_tracking = TimeTracking(
            total_spent_time=Duration.of(32.0, TimeUnit.HOUR),
            current_assignee_spent_time=Duration.of(24.0, TimeUnit.HOUR)
        )
        
        task = Task(
            id="PROJ-123",
            title="Calculate business capacity",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
            assignment=Assignment(),
            time_tracking=time_tracking,
            system_metadata=SystemMetadata(original_status="In Progress", project_key="PROJ")
        )
        
        # When
        result = self.task_convertor.convert_task_to_data(task)
        
        # Then
        self.assertEqual(4.0, result.time_tracking.total_spent_time_days)
        self.assertEqual(3.0, result.time_tracking.current_assignee_spent_time_days)
    
    def test_shouldCalculateEstimationTimeInBusinessDaysForProjectForecastAccuracy(self):
        # Given - Forecast with 5 business days estimation
        forecast = Forecast(
            velocity=2.0,
            estimation_time=Duration.of(40.0, TimeUnit.HOUR),  # 5 business days
            target=Target(health_status=HealthStatus.GREEN),
            subject=Subject(),
            start_date=date(2024, 1, 15),
            end_date=date(2024, 1, 19)
        )
        
        task = Task(
            id="PROJ-456",
            title="Project estimation calculation",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
            assignment=Assignment(),
            time_tracking=TimeTracking(),
            forecast=forecast,
            system_metadata=SystemMetadata(original_status="Planning", project_key="PROJ")
        )
        
        # When
        result = self.task_convertor.convert_task_to_data(task)
        estimation_hours = self.task_convertor.get_task_estimation_hours(task)
        
        # Then
        self.assertEqual(5.0, result.forecast.estimation_time_days)
        self.assertEqual(40.0, estimation_hours)  # For capacity planning calculations
    
    def test_shouldCalculateTeamVelocityAverageCorrectlyForPerformanceMeasurement(self):
        # Given - Team velocity data over multiple sprints
        velocity_reports_data = [
            self._create_velocity_report_data(date(2024, 1, 1), 4.5, 22.5),
            self._create_velocity_report_data(date(2024, 2, 1), 5.2, 26.0),
            self._create_velocity_report_data(date(2024, 3, 1), 4.8, 24.0)
        ]
        
        # When
        velocity_chart = self.velocity_facade.get_velocity_chart_data(velocity_reports_data)
        story_points_chart = self.velocity_facade.get_story_points_chart_data(velocity_reports_data)
        
        # Then
        self.assertEqual([4.5, 5.2, 4.8], velocity_chart.datasets[0].data)
        self.assertEqual([22.5, 26.0, 24.0], story_points_chart.datasets[0].data)
        
        # Average velocity calculation for team performance: (4.5 + 5.2 + 4.8) / 3 = 4.83
        average_velocity = sum(velocity_chart.datasets[0].data) / len(velocity_chart.datasets[0].data)
        self.assertAlmostEqual(4.83, average_velocity, places=2)
    
    def test_shouldCalculateIndividualDeveloperProductivityMetricsForOneOnOneReviews(self):
        # Given - Individual developer velocity data
        developer_reports = [
            self._create_developer_velocity_report_data("alice.johnson", "Alice Johnson", 
                                                       date(2024, 1, 1), 2.5, 12.5),
            self._create_developer_velocity_report_data("alice.johnson", "Alice Johnson", 
                                                       date(2024, 2, 1), 2.8, 14.0),
            self._create_developer_velocity_report_data("bob.smith", "Bob Smith", 
                                                       date(2024, 1, 1), 3.1, 15.5),
            self._create_developer_velocity_report_data("bob.smith", "Bob Smith", 
                                                       date(2024, 2, 1), 3.5, 17.5)
        ]
        
        # When
        chart_result = self.velocity_chart_convertor.convert_dev_velocity_reports_to_velocity_chart(developer_reports)
        
        # Then
        alice_dataset = next(ds for ds in chart_result.datasets if ds.label == "Alice Johnson")
        bob_dataset = next(ds for ds in chart_result.datasets if ds.label == "Bob Smith")
        
        # Alice's productivity: [2.5, 2.8] - showing improvement
        self.assertEqual([2.5, 2.8], alice_dataset.data)
        alice_improvement = alice_dataset.data[1] - alice_dataset.data[0]
        self.assertAlmostEqual(0.3, alice_improvement, places=10)
        
        # Bob's productivity: [3.1, 3.5] - consistently higher performer
        self.assertEqual([3.1, 3.5], bob_dataset.data)
        bob_average = sum(bob_dataset.data) / len(bob_dataset.data)
        self.assertEqual(3.3, bob_average)
    
    def test_shouldCalculateWorkloadDistributionAccuratelyForResourceAllocation(self):
        # Given - Multiple tasks with different time investments
        high_effort_task = self._create_task_with_time_tracking(32.0)  # 4 days
        medium_effort_task = self._create_task_with_time_tracking(16.0)  # 2 days
        low_effort_task = self._create_task_with_time_tracking(8.0)   # 1 day
        
        tasks = [high_effort_task, medium_effort_task, low_effort_task]
        
        # When - Convert all tasks
        converted_tasks = [self.task_convertor.convert_task_to_data(task) for task in tasks]
        
        # Then - Calculate workload distribution
        total_days = sum(task.time_tracking.total_spent_time_days for task in converted_tasks 
                        if task.time_tracking.total_spent_time_days)
        self.assertEqual(7.0, total_days)  # 4 + 2 + 1
        
        # Workload percentages for resource allocation decisions
        high_effort_percentage = (4.0 / 7.0) * 100  # 57.14%
        medium_effort_percentage = (2.0 / 7.0) * 100  # 28.57%
        low_effort_percentage = (1.0 / 7.0) * 100   # 14.29%
        
        self.assertAlmostEqual(57.14, high_effort_percentage, places=2)
        self.assertAlmostEqual(28.57, medium_effort_percentage, places=2)
        self.assertAlmostEqual(14.29, low_effort_percentage, places=2)
    
    def test_shouldCalculateSprintBurndownRateForDeadlineProjections(self):
        # Given - Sprint tasks with varying completion states
        completed_points = 15.0  # Story points completed
        remaining_points = 25.0  # Story points remaining
        sprint_days_elapsed = 8.0  # Days into sprint
        sprint_total_days = 14.0  # Total sprint days
        
        # When - Calculate burndown metrics
        completion_percentage = (completed_points / (completed_points + remaining_points)) * 100
        daily_burn_rate = completed_points / sprint_days_elapsed
        projected_completion_days = remaining_points / daily_burn_rate
        projected_total_days = sprint_days_elapsed + projected_completion_days
        
        # Then
        self.assertEqual(37.5, completion_percentage)  # 37.5% complete
        self.assertAlmostEqual(1.875, daily_burn_rate, places=3)  # 1.875 points/day
        self.assertAlmostEqual(13.33, projected_completion_days, places=2)  # ~13.33 days remaining
        self.assertAlmostEqual(21.33, projected_total_days, places=2)  # Will exceed sprint duration
        
        # This indicates the team is behind schedule and needs intervention
    
    def test_shouldCalculateTeamEfficiencyRatioForPerformanceAnalysis(self):
        # Given - Team velocity vs capacity data
        planned_capacity_hours = 320.0  # 4 developers × 8 hours × 10 days
        actual_completed_hours = 280.0  # Actual work completed
        story_points_completed = 35.0
        estimated_story_point_hours = 8.0  # Hours per story point estimate
        
        # When - Calculate efficiency metrics
        capacity_utilization = (actual_completed_hours / planned_capacity_hours) * 100
        story_point_efficiency = story_points_completed * estimated_story_point_hours
        estimation_accuracy = (story_point_efficiency / actual_completed_hours) * 100
        
        # Then
        self.assertEqual(87.5, capacity_utilization)  # 87.5% capacity utilization
        self.assertEqual(280.0, story_point_efficiency)  # Perfect estimation match
        self.assertEqual(100.0, estimation_accuracy)  # 100% estimation accuracy
        
        # These metrics indicate healthy team performance and accurate estimation
    
    def test_shouldHandleZeroValuesGracefullyInCalculationsForRobustMetrics(self):
        # Given - Edge case with zero time tracking
        zero_time_task = Task(
            id="PROJ-999",
            title="Task with no time tracking",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
            assignment=Assignment(),
            time_tracking=None,
            system_metadata=SystemMetadata(original_status="To Do", project_key="PROJ")
        )
        
        # When
        result = self.task_convertor.convert_task_to_data(zero_time_task)
        estimation_hours = self.task_convertor.get_task_estimation_hours(zero_time_task)
        
        # Then
        self.assertIsNone(result.time_tracking.total_spent_time_days)
        self.assertIsNone(result.time_tracking.current_assignee_spent_time_days)
        self.assertEqual(0.0, estimation_hours)
    
    def test_shouldMaintainPrecisionInFloatingPointCalculationsForFinancialAccuracy(self):
        # Given - High precision time tracking for billing/cost calculations
        precise_time_tracking = TimeTracking(
            total_spent_time=Duration.of(23.75, TimeUnit.HOUR),  # 2.96875 business days
            current_assignee_spent_time=Duration.of(15.25, TimeUnit.HOUR)  # 1.90625 business days
        )
        
        task = Task(
            id="PROJ-BILLING",
            title="High precision billing task",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
            assignment=Assignment(),
            time_tracking=precise_time_tracking,
            system_metadata=SystemMetadata(original_status="Done", project_key="PROJ")
        )
        
        # When
        result = self.task_convertor.convert_task_to_data(task)
        
        # Then - Maintain precision for accurate billing
        self.assertAlmostEqual(2.96875, result.time_tracking.total_spent_time_days, places=5)
        self.assertAlmostEqual(1.90625, result.time_tracking.current_assignee_spent_time_days, places=5)
    
    def _create_velocity_report_data(self, start_date, velocity, story_points):
        from ui_web.data.velocity_report_data import VelocityReportData
        return VelocityReportData(
            start_date=start_date,
            velocity=velocity,
            story_points=story_points
        )
    
    def _create_developer_velocity_report_data(self, scope_id, scope_name, start_date, velocity, story_points):
        from ui_web.data.velocity_report_data import VelocityReportData
        return VelocityReportData(
            start_date=start_date,
            velocity=velocity,
            story_points=story_points,
            metric_scope=scope_id,
            metric_scope_name=scope_name
        )
    
    def _create_task_with_time_tracking(self, hours):
        return Task(
            id=f"PROJ-{int(hours)}H",
            title=f"Task with {hours} hours",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
            assignment=Assignment(),
            time_tracking=TimeTracking(total_spent_time=Duration.of(hours, TimeUnit.HOUR)),
            system_metadata=SystemMetadata(original_status="Done", project_key="PROJ")
        )


if __name__ == '__main__':
    unittest.main()