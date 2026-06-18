import unittest

from tasks.app.domain.model.config import MemberGroupConfig
from ui_web.utils.available_member_stage_filter import AvailableMemberStageFilter


def _member_group_config() -> MemberGroupConfig:
    members = {
        "alice.developer": {"level": "senior", "member_groups": ["Headless"], "stages": ["Development"]},
        "diana.qa": {"level": "middle", "member_groups": ["Headless"], "stages": ["Validation"]},
        "bob.manager": {"level": "lead", "member_groups": ["Headless"], "stages": ["Analysis"]},
        "carol.untagged": {"level": "middle", "member_groups": ["Headless"]},
    }
    return MemberGroupConfig(members=members, default_member_group_when_missing=None)


class TestAvailableMemberStageFilter(unittest.TestCase):

    def test_shouldReturnAllMembersWhenNoAllowedStagesConfigured(self):
        # given
        stage_filter = AvailableMemberStageFilter(_member_group_config(), allowed_stages=[])
        candidate_members = ["alice.developer", "bob.manager", "carol.untagged"]

        # when
        result = stage_filter.filter(candidate_members)

        # then
        self.assertEqual(candidate_members, result)

    def test_shouldKeepOnlyMembersWorkingInAllowedStagesWhenConfigured(self):
        # given
        stage_filter = AvailableMemberStageFilter(_member_group_config(), allowed_stages=["Development", "Validation"])
        candidate_members = ["alice.developer", "diana.qa", "bob.manager"]

        # when
        result = stage_filter.filter(candidate_members)

        # then
        self.assertEqual(["alice.developer", "diana.qa"], result)

    def test_shouldExcludeMembersWithNoStagesWhenFilterConfigured(self):
        # given
        stage_filter = AvailableMemberStageFilter(_member_group_config(), allowed_stages=["Development"])
        candidate_members = ["alice.developer", "carol.untagged"]

        # when
        result = stage_filter.filter(candidate_members)

        # then
        self.assertEqual(["alice.developer"], result)
