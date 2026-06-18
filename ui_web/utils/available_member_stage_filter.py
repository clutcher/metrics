from typing import List

from tasks.app.domain.model.config import MemberGroupConfig


class AvailableMemberStageFilter:

    def __init__(self, member_group_config: MemberGroupConfig, allowed_stages: List[str]) -> None:
        self._member_group_config = member_group_config
        self._allowed_stages = allowed_stages

    def filter(self, member_ids: List[str]) -> List[str]:
        if not self._allowed_stages:
            return member_ids

        allowed_ids = self._member_group_config.get_members_in_stages(self._allowed_stages)
        return [member_id for member_id in member_ids if member_id in allowed_ids]
