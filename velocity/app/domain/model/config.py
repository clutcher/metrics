from dataclasses import dataclass
from typing import List, Dict


@dataclass(slots=True)
class CalculationConfig:
    working_days_per_month: int
    default_story_points_value_when_missing: float


@dataclass(slots=True)
class WorkflowConfig:
    done_status_codes: List[str]


@dataclass(slots=True)
class MemberVelocityConfig:
    story_points_to_ideal_hours_ratio: float
    seniority_levels: Dict[str, float]
    members: Dict[str, Dict]
    default_seniority_level: str


@dataclass(slots=True)
class VelocityConfig:
    calculation: CalculationConfig
    workflow: WorkflowConfig
    member_velocity: MemberVelocityConfig
