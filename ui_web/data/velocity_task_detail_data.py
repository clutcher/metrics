from dataclasses import dataclass
from typing import Optional

from .task_data import TaskData


@dataclass(slots=True)
class TaskVelocityData(TaskData):
    developer_story_points: float = 0.0
    developer_time_hours: float = 0.0


@dataclass(slots=True)
class DeveloperVelocitySummary:
    total_story_points: float
    total_time_hours: float
    velocity: Optional[float]
