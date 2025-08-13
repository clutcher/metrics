from dataclasses import dataclass
from typing import Optional, Dict, List

from sd_metrics_lib.utils.time import Duration


@dataclass(slots=True)
class Assignee:
    id: str
    display_name: str
    avatar_url: Optional[str] = None


@dataclass(slots=True)
class TimeTracking:
    total_spent_time: Optional[Duration] = None
    spent_time_by_assignee: Optional[Dict[str, Duration]] = None
    current_assignee_spent_time: Optional[Duration] = None


@dataclass(slots=True)
class Assignment:
    assignee: Optional[Assignee] = None


@dataclass(slots=True)
class Task:
    id: str
    title: str
    story_points: Optional[float] = None
    assignment: Assignment = None
    time_tracking: TimeTracking = None
    child_tasks: Optional[List['Task']] = None
    forecast: Optional['Forecast'] = None
