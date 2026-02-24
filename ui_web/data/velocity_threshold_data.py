from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class VelocityLevelThreshold:
    level_name: str
    threshold: float
    color: str


@dataclass(slots=True)
class VelocityThresholdsData:
    thresholds: List[VelocityLevelThreshold]
