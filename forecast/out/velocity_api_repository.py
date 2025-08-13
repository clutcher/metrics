from typing import Optional

from sd_metrics_lib.utils.time import TimeUnit

from velocity.app.domain.model.velocity import ReportGenerationParameters, ReportType
from ..app.domain.model.enums import VelocityStrategy, SubjectType
from ..app.domain.model.forecast import Subject
from ..app.spi.velocity_repository import VelocityRepository


class VelocityApiRepository(VelocityRepository):

    def __init__(self, velocity_report_api, velocity_calculation_api):
        self._velocity_report_api = velocity_report_api
        self._velocity_calculation_api = velocity_calculation_api

    async def get_velocity(self, velocity_strategy: VelocityStrategy, time_unit: TimeUnit, subject: Subject) -> \
    Optional[float]:
        if velocity_strategy == VelocityStrategy.REAL_VELOCITY:
            return await self._get_real_velocity(subject)
        elif velocity_strategy == VelocityStrategy.IDEAL_VELOCITY:
            return await self._get_ideal_velocity(subject, time_unit)
        return None

    async def _get_real_velocity(self, subject: Subject) -> Optional[float]:
        parameters = ReportGenerationParameters(
            time_unit=TimeUnit.MONTH,
            number_of_periods=3,
            report_type=await self._resolve_report_type(subject.type),
            scope_id=subject.id
        )

        velocity_reports = await self._velocity_report_api.generate_velocity_report(parameters)

        if velocity_reports and len(velocity_reports) > 0:
            total_velocity = sum(report.velocity for report in velocity_reports)
            return total_velocity / len(velocity_reports)

        return None

    async def _get_ideal_velocity(self, subject: Subject, time_unit: TimeUnit) -> Optional[float]:
        return await self._velocity_calculation_api.calculate_ideal_velocity(subject.id, time_unit)

    @staticmethod
    async def _resolve_report_type(subject_type: SubjectType) -> ReportType:
        if subject_type == SubjectType.MEMBER:
            return ReportType.MEMBER_SCOPE

        return ReportType.MEMBER_GROUP_SCOPE
