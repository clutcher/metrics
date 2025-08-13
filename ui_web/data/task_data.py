from dataclasses import dataclass
from typing import List, Optional

from sd_metrics_lib.utils.enums import HealthStatus

from .member_data import MemberGroupData


@dataclass(slots=True)
class AssigneeData:
    id: str
    display_name: str
    avatar_url: Optional[str] = None


@dataclass(slots=True)
class AssignmentData:
    assignee: Optional[AssigneeData] = None
    member_group: Optional[MemberGroupData] = None


@dataclass(slots=True)
class TimeTrackingData:
    total_spent_time_days: Optional[float] = None
    current_assignee_spent_time_days: Optional[float] = None


@dataclass(slots=True)
class SystemMetadataData:
    original_status: str
    url: Optional[str] = None


@dataclass(slots=True)
class ForecastData:
    health_status: Optional[HealthStatus] = None
    estimation_time_days: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    velocity: Optional[float] = None


@dataclass(slots=True)
class TaskData:
    id: str
    title: str
    assignment: AssignmentData
    time_tracking: TimeTrackingData
    system_metadata: SystemMetadataData
    story_points: Optional[float] = None
    child_tasks: Optional[List['TaskData']] = None
    child_tasks_count: int = 0
    stage: Optional[str] = None
    forecast: Optional[ForecastData] = None


