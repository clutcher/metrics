from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sd_metrics_lib.utils.enums import HealthStatus
from sd_metrics_lib.utils.time import TimeUnit, Duration

from .enums import TargetType, SubjectType, VelocityStrategy, StoryPointsStrategy


@dataclass(slots=True)
class Target:
    type: TargetType = TargetType.TASK
    id: str = ""
    health_status: Optional[HealthStatus] = None


@dataclass(slots=True)
class Subject:
    type: SubjectType = SubjectType.MEMBER
    id: str = ""


@dataclass(slots=True)
class Forecast:
    velocity: float
    estimation_time: Duration
    target: Target
    subject: Subject
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass(slots=True)
class ForecastGenerationParameters:
    velocity_strategy: VelocityStrategy
    story_points_strategy: StoryPointsStrategy
    subject: Subject
    time_unit: TimeUnit
    start_date: datetime = datetime.now()
