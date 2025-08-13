import unittest

from sd_metrics_lib.utils.time import TimeUnit, TimePolicy

from velocity.app.domain.velocity_calculation_service import VelocityCalculationService
from velocity.tests.fixtures.velocity_builders import VelocityConfigBuilder


class TestApiVelocityCalculation(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.ideal_time_policy = TimePolicy.BUSINESS_HOURS

    async def test_shouldCalculateHighVelocityForSeniorDeveloperInSprintPlanning(self):
        config = VelocityConfigBuilder.sprint_planning_team().build()
        service = VelocityCalculationService(config, self.ideal_time_policy)
        
        result = await service.calculate_ideal_velocity("alice", TimeUnit.MONTH)
        
        self.assertIsNotNone(result)
        self.assertGreater(result, 0.0)

    async def test_shouldCalculateStandardVelocityForJuniorDeveloperInSprintPlanning(self):
        config = VelocityConfigBuilder.sprint_planning_team().build()
        service = VelocityCalculationService(config, self.ideal_time_policy)
        
        result = await service.calculate_ideal_velocity("carol", TimeUnit.MONTH)
        
        self.assertIsNotNone(result)
        self.assertGreater(result, 0.0)

    async def test_shouldCalculateHigherVelocityForSeniorThanJuniorInRetrospectiveTeam(self):
        config = VelocityConfigBuilder.retrospective_team().build()
        service = VelocityCalculationService(config, self.ideal_time_policy)
        
        senior_velocity = await service.calculate_ideal_velocity("eve", TimeUnit.WEEK)
        junior_velocity = await service.calculate_ideal_velocity("grace", TimeUnit.WEEK)
        
        self.assertIsNotNone(senior_velocity)
        self.assertIsNotNone(junior_velocity)
        self.assertGreater(senior_velocity, junior_velocity)

    async def test_shouldFallbackToDefaultLevelForUnknownMember(self):
        config = VelocityConfigBuilder.sprint_planning_team().build()
        service = VelocityCalculationService(config, self.ideal_time_policy)
        
        result = await service.calculate_ideal_velocity("unknown-dev", TimeUnit.MONTH)

        self.assertIsNotNone(result)
        self.assertGreater(result, 0.0)

    async def test_shouldCalculateVelocityInDifferentTimeUnitsForRetrospectiveAnalysis(self):
        config = VelocityConfigBuilder.retrospective_team().build()
        service = VelocityCalculationService(config, self.ideal_time_policy)
        
        monthly_velocity = await service.calculate_ideal_velocity("eve", TimeUnit.MONTH)
        weekly_velocity = await service.calculate_ideal_velocity("eve", TimeUnit.WEEK)
        
        self.assertIsNotNone(monthly_velocity)
        self.assertIsNotNone(weekly_velocity)
        self.assertGreater(monthly_velocity, weekly_velocity)


if __name__ == '__main__':
    unittest.main()