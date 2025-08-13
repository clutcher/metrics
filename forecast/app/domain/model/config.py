from dataclasses import dataclass
from typing import Dict


@dataclass(slots=True)
class SeniorityConfig:
    seniority_levels: Dict[str, float]
    default_seniority_level_when_missing: str


@dataclass(slots=True)
class CalculationConfig:
    ideal_hours_per_day: float
    story_points_to_ideal_hours_convertion_ratio: float
    default_story_points_value_when_missing: float
    default_health_status_when_missing: str


@dataclass(slots=True)
class ForecastConfig:
    seniority: SeniorityConfig
    calculation: CalculationConfig
