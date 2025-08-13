from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

from sd_metrics_lib.utils.time import Duration


@dataclass(slots=True)
class Assignee:
    id: str
    display_name: str


@dataclass(slots=True)
class Assignment:
    assignee: Optional[Assignee] = None


@dataclass(slots=True)
class TimeTracking:
    total_spent_time: Optional[Duration] = None
    spent_time_by_assignee: Optional[Dict[str, Duration]] = None


@dataclass(slots=True)
class Task:
    id: str
    title: str
    completed_at: datetime
    story_points: Optional[float] = None
    assignment: Optional[Assignment] = None
    time_tracking: Optional[TimeTracking] = None
