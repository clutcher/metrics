import unittest

from tasks.app.domain.model.config import MemberGroupConfig

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

    def test_shouldResolveCustomFilterWhenMemberGroupHasCustomFilterConfigured(self):
        # Given
        config = MemberGroupConfig(
            members={"alice": {"member_groups": ["headless-team"]}},
            default_member_group_when_missing=None,
            custom_filters={"headless-team": "[System.Parent] IN (164284, 172447)"}
        )
        resolver = MemberGroupResolver(config)

        # When
        result = resolver.resolve_custom_filter("headless-team")

        # Then
        self.assertEqual("[System.Parent] IN (164284, 172447)", result)

    def test_shouldReturnNoneWhenMemberGroupHasNoCustomFilter(self):
        # Given
        config = MemberGroupConfig(
            members={"alice": {"member_groups": ["development-team"]}},
            default_member_group_when_missing=None,
            custom_filters={"headless-team": "[System.Parent] IN (164284)"}
        )
        resolver = MemberGroupResolver(config)

        # When
        result = resolver.resolve_custom_filter("development-team")

        # Then
        self.assertIsNone(result)

    def test_shouldReturnNoneWhenNoCustomFiltersConfigured(self):
        # Given
        config = MemberGroupConfig(
            members={"alice": {"member_groups": ["development-team"]}},
            default_member_group_when_missing=None
        )
        resolver = MemberGroupResolver(config)

        # When
        result = resolver.resolve_custom_filter("development-team")

        # Then
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
