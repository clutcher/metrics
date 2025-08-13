from abc import ABC, abstractmethod
from typing import Optional

from sd_metrics_lib.utils.time import TimeUnit

from ..domain.model.enums import VelocityStrategy
from ..domain.model.forecast import Subject


class VelocityRepository(ABC):

    @abstractmethod
    async def get_velocity(self, velocity_strategy: VelocityStrategy, time_unit: TimeUnit, subject: Subject) -> Optional[float]:
        pass