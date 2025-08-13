from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.model.velocity import ReportGenerationParameters, VelocityReport


class ApiForVelocityReportGeneration(ABC):

    @abstractmethod
    async def generate_velocity_report(self, request: ReportGenerationParameters) -> Optional[List[VelocityReport]]:
        pass
