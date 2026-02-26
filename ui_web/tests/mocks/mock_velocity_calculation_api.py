from typing import Optional
from unittest.mock import AsyncMock

from sd_metrics_lib.utils.time import TimeUnit

from velocity.app.api.api_for_velocity_calculation import ApiForVelocityCalculation


class MockVelocityCalculationApi(ApiForVelocityCalculation):

    def __init__(self):
        self._mock = AsyncMock()

    async def calculate_ideal_velocity(self, member_id: str, time_unit: TimeUnit) -> Optional[float]:
        return await self._mock.calculate_ideal_velocity(member_id, time_unit)

    @property
    def mock(self) -> AsyncMock:
        return self._mock
