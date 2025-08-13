from typing import Optional
from unittest.mock import AsyncMock

from sd_metrics_lib.utils.time import TimeUnit

from forecast.app.domain.model.enums import VelocityStrategy
from forecast.app.domain.model.forecast import Subject
from forecast.app.spi.velocity_repository import VelocityRepository


class MockVelocityRepository(VelocityRepository):
    
    def __init__(self):
        self._mock = AsyncMock()
        
    async def get_velocity(
        self,
        velocity_strategy: VelocityStrategy,
        time_unit: TimeUnit,
        subject: Subject
    ) -> Optional[float]:
        return await self._mock.get_velocity(velocity_strategy, time_unit, subject)
    
    @property
    def mock(self) -> AsyncMock:
        return self._mock