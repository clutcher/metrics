from dataclasses import dataclass
from typing import Optional, List


@dataclass(slots=True)
class MemberGroupData:
    id: str
    name: str


@dataclass(slots=True)
class MemberData:
    member_id: str
    display_name: str
    total_hours_last_30: Optional[float] = None
    tickets_assigned_last_30: Optional[int] = None
    hours_per_task: Optional[float] = None
    total_work_days_last_30: Optional[float] = None


@dataclass(slots=True)
class MemberGroupFilterData:
    selected_member_group_id: Optional[str]
    available_member_groups: List[MemberGroupData]