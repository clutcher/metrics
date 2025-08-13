from typing import List
from unittest.mock import AsyncMock


class MockVelocityApi:
    
    def __init__(self):
        self._mock = AsyncMock()
        
    async def generate_velocity_report(self, parameters) -> List:
        return await self._mock.generate_velocity_report(parameters)
    
    @property
    def mock(self) -> AsyncMock:
        return self._mock