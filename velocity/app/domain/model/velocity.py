from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Optional

from sd_metrics_lib.utils.time import TimeUnit


class ReportType(Enum):
    MEMBER_GROUP_SCOPE = auto()
    MEMBER_SCOPE = auto()


@dataclass(slots=True)
class ReportGenerationParameters:
    time_unit: TimeUnit
    number_of_periods: int
    report_type: ReportType = None
    scope_id: Optional[str] = None


@dataclass(slots=True)
class MetricCalculationReport:
    start_date: datetime
    end_date: datetime
    metric_value: float


@dataclass(slots=True)
class VelocityReport:
    start_date: datetime
    end_date: datetime
    velocity: float
    story_points: float
    metric_scope: Optional[str] = None
    metric_scope_name: Optional[str] = None
