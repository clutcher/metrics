from django.conf import settings
from sd_metrics_lib.utils.time import TimePolicy

from tasks.container import tasks_container
from velocity.app.domain.calculation.member_group_resolver import MemberGroupResolver
from .app.domain.model.config import MemberVelocityConfig
from .app.api.api_for_report_generation import ApiForVelocityReportGeneration
from .app.api.api_for_velocity_calculation import ApiForVelocityCalculation
from .app.domain.calculation.velocity_report_calculator import VelocityReportCalculator
from .app.domain.report_generation_service import ReportGenerationService
from .app.domain.velocity_calculation_service import VelocityCalculationService
from .config_loader import load_velocity_config
from .out.tasks_api_repository import TasksApiRepository


class VelocityContainer:

    def __init__(self):
        self._config = load_velocity_config()

    @property
    def velocity_report_generation_api(self) -> ApiForVelocityReportGeneration:
        return ReportGenerationService(
            calculation_service=self._calculation_service
        )

    @property
    def velocity_calculation_api(self) -> ApiForVelocityCalculation:
        return VelocityCalculationService(self._config.member_velocity, self.ideal_time_policy)

    @property
    def _calculation_service(self) -> VelocityReportCalculator:
        return VelocityReportCalculator(
            task_repository=self._task_repository,
            configuration=self._config,
            member_group_resolver=self._member_group_resolver,
            velocity_search_criteria_factory=tasks_container.create_velocity_search_criteria
        )

    @property
    def _task_repository(self) -> TasksApiRepository:
        return TasksApiRepository(tasks_container.task_search_api)

    @property
    def _member_group_resolver(self) -> MemberGroupResolver:
        return MemberGroupResolver(tasks_container.get_member_group_config())

    def get_member_velocity_config(self) -> MemberVelocityConfig:
        return self._config.member_velocity

    @property
    def ideal_time_policy(self) -> TimePolicy:
        return TimePolicy(
            hours_per_day=settings.METRICS_IDEAL_HOURS_PER_DAY,
            days_per_week=5,
            days_per_month=settings.METRICS_WORKING_DAYS_PER_MONTH
        )


velocity_container = VelocityContainer()
