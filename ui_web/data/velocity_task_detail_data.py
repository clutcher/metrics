from dataclasses import dataclass
from typing import Optional

from .task_data import TaskData


@dataclass(slots=True)
class TaskVelocityData(TaskData):
    developer_story_points: float = 0.0
    developer_time_days: float = 0.0
    total_estimated_days: Optional[float] = None
    estimated_days: Optional[float] = None
    deviation_percent: Optional[float] = None


@dataclass(slots=True)
class DeveloperVelocitySummary:
    total_story_points: float
    total_time_days: float
    velocity: Optional[float]
    total_task_story_points: Optional[float] = None
    total_estimated_days: Optional[float] = None
    average_deviation_percent: Optional[float] = None
    working_days: Optional[float] = None
    working_days_in_month: Optional[int] = None
    workload_percent: Optional[float] = None
