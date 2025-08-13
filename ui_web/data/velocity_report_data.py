from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(slots=True)
class VelocityReportData:
    start_date: date
    velocity: float
    story_points: float
    metric_scope: Optional[str] = None
    metric_scope_name: Optional[str] = None