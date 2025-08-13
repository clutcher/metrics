from abc import ABC, abstractmethod
from typing import Optional

from sd_metrics_lib.utils.time import TimeUnit


class ApiForVelocityCalculation(ABC):

    @abstractmethod
    async def calculate_ideal_velocity(self, member_id: str, time_unit: TimeUnit) -> Optional[float]:
        pass