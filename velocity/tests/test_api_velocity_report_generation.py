import unittest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta

from velocity.app.domain.calculation.member_group_resolver import MemberGroupResolver
from velocity.app.domain.calculation.velocity_report_calculator import VelocityReportCalculator
from velocity.app.domain.report_generation_service import ReportGenerationService
from velocity.tests.fixtures.velocity_builders import (
    ReportParametersBuilder, 
    VelocityConfigBuilder, 
    BusinessScenarios
)
from velocity.tests.mocks.mock_task_repository import MockTaskRepository


class MockVelocityReportCalculator:
    def __init__(self):
        self.mock = AsyncMock()
        self.calculate_velocity_report_for_period = AsyncMock()
        self.calculate_scoped_velocity_reports_for_period = AsyncMock()


class TestApiVelocityReportGeneration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.task_repository = MockTaskRepository()
        self.config = VelocityConfigBuilder.sprint_planning_team().build()
        self.member_group_resolver = MemberGroupResolver(self.config)
        self.velocity_calculator = MockVelocityReportCalculator()
        
        self.report_service = ReportGenerationService(self.velocity_calculator)

    async def test_shouldGenerateSprintPlanningReportForDevelopmentTeam(self):
        parameters = (ReportParametersBuilder.sprint_planning_report()
                     .for_scope("development-team")
                     .build())
        
        self.velocity_calculator.calculate_velocity_report_for_period.return_value = self._create_sample_report()
        
        result = await self.report_service.generate_velocity_report(parameters)
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        self.velocity_calculator.calculate_velocity_report_for_period.assert_called()

    async def test_shouldGenerateRetrospectiveAnalysisReportForIndividualMembers(self):
        parameters = (ReportParametersBuilder.retrospective_analysis()
                     .for_scope("development-team")
                     .build())
        
        self.velocity_calculator.calculate_scoped_velocity_reports_for_period.return_value = [self._create_sample_report()]
        
        result = await self.report_service.generate_velocity_report(parameters)
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)
        self.velocity_calculator.calculate_scoped_velocity_reports_for_period.assert_called()

    async def test_shouldReturnNoReportsWhenCapacityPlanningWithoutReportType(self):
        parameters = (ReportParametersBuilder()
                     .over_last_months(3)
                     .for_scope("development-team")
                     .build())
        parameters.report_type = None
        
        result = await self.report_service.generate_velocity_report(parameters)
        
        self.assertIsNone(result)

    async def test_shouldGenerateMultiplePeriodsForSprintPlanningAnalysis(self):
        parameters = (ReportParametersBuilder.sprint_planning_report()
                     .over_last_months(6)
                     .for_scope("development-team")
                     .build())
        
        self.velocity_calculator.calculate_velocity_report_for_period.return_value = self._create_sample_report()
        
        result = await self.report_service.generate_velocity_report(parameters)
        
        self.assertIsNotNone(result)
        call_count = self.velocity_calculator.calculate_velocity_report_for_period.call_count
        self.assertEqual(6, call_count)

    def _create_sample_report(self):
        from velocity.app.domain.model.velocity import VelocityReport
        return VelocityReport(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            velocity=15.5,
            story_points=45.0,
            metric_scope="development-team",
            metric_scope_name="Development Team"
        )


if __name__ == '__main__':
    unittest.main()