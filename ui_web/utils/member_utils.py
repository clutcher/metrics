from typing import Dict, Optional

from django.conf import settings


class MemberUtils:

    @staticmethod
    def get_all_members_of_member_group(member_group_filter: Optional[str] = None) -> Dict[str, Dict]:
        all_members = settings.METRICS_MEMBERS

        if not member_group_filter or member_group_filter == "":
            return all_members

        filtered_members = {}
        for member_id, member_config in all_members.items():
            member_groups = member_config.get('member_groups', [])
            if member_group_filter in member_groups:
                filtered_members[member_id] = member_config

        return filtered_members