import unittest

from velocity.app.domain.calculation.member_group_resolver import MemberGroupResolver
from velocity.tests.fixtures.velocity_builders import VelocityConfigBuilder


class TestMemberGroupResolver(unittest.TestCase):

    def test_shouldResolveSprintPlanningTeamMembersWhenDevelopmentTeamRequested(self):
        config = VelocityConfigBuilder.sprint_planning_team().build()
        resolver = MemberGroupResolver(config)
        
        result = resolver.resolve_members("development-team")
        
        self.assertEqual(4, len(result))
        self.assertIn("alice", result)
        self.assertIn("bob", result)
        self.assertIn("carol", result)
        self.assertIn("dave", result)

    def test_shouldResolveRetrospectiveTeamMembersWhenDevelopmentTeamRequested(self):
        config = VelocityConfigBuilder.retrospective_team().build()
        resolver = MemberGroupResolver(config)
        
        result = resolver.resolve_members("development-team")
        
        self.assertEqual(3, len(result))
        self.assertIn("eve", result)
        self.assertIn("frank", result)
        self.assertIn("grace", result)

    def test_shouldReturnEmptyResultWhenCapacityPlanningTeamHasNoMatchingGroup(self):
        config = VelocityConfigBuilder.sprint_planning_team().build()
        resolver = MemberGroupResolver(config)
        
        result = resolver.resolve_members("qa-team")
        
        self.assertIsNone(result)

    def test_shouldReturnEmptyResultWhenSprintPlanningWithoutMemberGroupConfiguration(self):
        config = VelocityConfigBuilder().with_senior_members([]).with_junior_members([]).build()
        resolver = MemberGroupResolver(config)
        
        result = resolver.resolve_members("development-team")
        
        self.assertIsNone(result)

    def test_shouldReturnEmptyResultWhenRetrospectiveAnalysisRequestsUnknownGroup(self):
        config = VelocityConfigBuilder.retrospective_team().build()
        resolver = MemberGroupResolver(config)
        
        result = resolver.resolve_members("management-team")
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()