from typing import Optional, List


class MemberGroupResolver:
    def __init__(self, member_group_config):
        self.member_group_config = member_group_config

    def resolve_members(self, member_group_id: Optional[str]) -> Optional[List[str]]:
        if not member_group_id or not self.member_group_config:
            return None

        assignees = []
        for member, member_data in self.member_group_config.members.items():
            member_groups = member_data.get('member_groups', [])
            if member_group_id in member_groups:
                assignees.append(member)

        return assignees if assignees else None