from tasks.container import tasks_container
from velocity.container import velocity_container
from .app.api.api_for_forecast import ApiForForecast
from .app.domain.forecast_service import ForecastService
from .config_loader import load_forecast_config
from .out.tasks_api_repository import TasksApiRepository
from .out.velocity_api_repository import VelocityApiRepository


class ForecastContainer:

    @property
    def forecast_api(self) -> ApiForForecast:
        return ForecastService(
            task_repository=self._task_repository,
            velocity_repository=self._velocity_repository,
            config=load_forecast_config(),
            ideal_time_policy=velocity_container.ideal_time_policy
        )

    @property
    def _task_repository(self) -> TasksApiRepository:
        return TasksApiRepository(
            tasks_container.task_search_api,
            tasks_container.task_hierarchy_api
        )

    @property
    def _velocity_repository(self) -> VelocityApiRepository:
        return VelocityApiRepository(
            velocity_container.velocity_report_generation_api,
            velocity_container.velocity_calculation_api
        )


forecast_container = ForecastContainer()