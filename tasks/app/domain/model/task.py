from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Tuple

from sd_metrics_lib.utils.time import Duration


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


class WorkTimeExtractorType(Enum):
    SIMPLE = "simple"
    BOUNDARY_FROM_LAST_MODIFIED = "boundary_from_last_modified"
    BOUNDARY_FROM_RESOLUTION = "boundary_from_resolution"


@dataclass(slots=True)
class Assignee:
    id: str
    display_name: str
    avatar_url: Optional[str] = None
    workload_days: Optional[Duration] = None


@dataclass(slots=True)
class Team:
    id: str
    name: str


@dataclass(slots=True)
class MemberGroup:
    id: str
    name: str


@dataclass(slots=True)
class TimeTracking:
    total_spent_time: Optional[Duration] = None
    spent_time_by_assignee: Optional[Dict[str, Duration]] = None
    current_assignee_spent_time: Optional[Duration] = None


@dataclass(slots=True)
class Assignment:
    assignee: Optional[Assignee] = None
    member_group: Optional[MemberGroup] = None


@dataclass(slots=True)
class SystemMetadata:
    original_status: str
    project_key: str
    url: Optional[str] = None


@dataclass(slots=True)
class Task:
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    system_metadata: SystemMetadata
    assignment: Assignment
    time_tracking: TimeTracking
    
    status: Optional[TaskStatus] = None
    stage: Optional[str] = None
    story_points: Optional[float] = None
    child_tasks_count: Optional[int] = None
    child_tasks: Optional[List['Task']] = None
    
    # Duck typing placeholder for forecast data
    forecast: Optional['Forecast'] = None


@dataclass(slots=True)
class TaskSearchCriteria:
    status_filter: Optional[List[str]] = None
    type_filter: Optional[List[str]] = None
    team_filter: Optional[List[str]] = None
    assignee_filter: Optional[List[str]] = None
    assignees_history_filter: Optional[List[str]] = None
    id_filter: Optional[List[str]] = None
    last_modified_date_range: Optional[Tuple[Optional[datetime], Optional[datetime]]] = None
    resolution_date_range: Optional[Tuple[Optional[datetime], Optional[datetime]]] = None


@dataclass(slots=True)
class EnrichmentOptions:
    include_time_tracking: bool = True
    worktime_extractor_type: Optional[WorkTimeExtractorType] = None
    worklog_transition_statuses: Optional[List[str]] = None


@dataclass(slots=True)
class HierarchyTraversalCriteria:
    max_depth: int = 5
    only_tasks_with_story_points: bool = False
    exclude_done_tasks: bool = True
