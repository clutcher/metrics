from datetime import datetime, timedelta
from typing import List, Optional

from sd_metrics_lib.utils.time import TimeUnit, TimePolicy, Duration

from .calculation.estimation import EstimationTimeCalculator
from .calculation.health import HealthStatusCalculator
from .model.config import ForecastConfig
from .model.enums import StoryPointsStrategy
from .model.enums import VelocityStrategy
from .model.forecast import Forecast, Target, ForecastGenerationParameters
from .model.task import Task
from ..api.api_for_forecast import ApiForForecast
from ..spi.task_repository import TaskRepository
from ..spi.velocity_repository import VelocityRepository


class ForecastService(ApiForForecast):

    def __init__(self, task_repository: TaskRepository, velocity_repository: VelocityRepository,
                 config: ForecastConfig, ideal_time_policy: TimePolicy):
        self._task_repository = task_repository
        self._velocity_repository = velocity_repository
        self._config = config
        self._ideal_time_policy = ideal_time_policy

    async def generate_forecasts_for_task_ids(self, task_ids: List[str], parameters: ForecastGenerationParameters) -> \
            List[Task]:
        tasks = await self._get_tasks(parameters, task_ids)
        return await self.generate_forecasts_for_tasks(tasks, parameters)

    async def generate_forecasts_for_tasks(self, tasks: List[Task], parameters: ForecastGenerationParameters) -> List[
        Task]:
        velocity = await self._velocity_repository.get_velocity(
            parameters.velocity_strategy,
            parameters.time_unit,
            parameters.subject
        )

        if velocity is None:
            return tasks

        for task in tasks:
            self._populate_direct_forecasts_recursive(task, velocity, parameters)

        if parameters.story_points_strategy == StoryPointsStrategy.CUMULATIVE:
            for task in tasks:
                self._aggregate_forecasts_bottom_up(task, velocity, parameters)

        for task in tasks:
            self._calculate_sequential_dates(task, parameters.start_date, parameters)

        return tasks

    def _populate_direct_forecasts_recursive(self, task: Task, velocity: float,
                                             parameters: ForecastGenerationParameters):
        task.forecast = self._create_forecast(task, velocity, parameters)

        if task.child_tasks:
            for child_task in task.child_tasks:
                self._populate_direct_forecasts_recursive(child_task, velocity, parameters)

    @staticmethod
    def _create_forecast(task: Task, velocity: float, parameters: ForecastGenerationParameters):
        story_points = task.story_points
        if not story_points:
            return None

        estimation_time = EstimationTimeCalculator.estimate(story_points, velocity, parameters.time_unit)
        if not estimation_time:
            return None

        total_spent_time = ForecastService._create_total_spent_time(task)
        health_status = HealthStatusCalculator.calculate(estimation_time, total_spent_time)

        return Forecast(
            velocity=velocity,
            estimation_time=estimation_time,
            target=Target(
                id=task.id,
                health_status=health_status
            ),
            subject=parameters.subject
        )

    def _aggregate_forecasts_bottom_up(self, task: Task, velocity: float, parameters: ForecastGenerationParameters):
        if not task.child_tasks:
            return

        for child_task in task.child_tasks:
            self._aggregate_forecasts_bottom_up(child_task, velocity, parameters)

        if task.forecast:
            return

        total_child_estimation_time = sum(
            self.__extract_forecasted_time(child_task, parameters.time_unit) for child_task in task.child_tasks
        )

        if total_child_estimation_time <= 0:
            return

        aggregated_time = Duration.of(total_child_estimation_time, parameters.time_unit)

        task.forecast = Forecast(
            velocity=velocity,
            estimation_time=aggregated_time,
            target=Target(
                id=task.id
            ),
            subject=parameters.subject
        )

    @staticmethod
    def __extract_forecasted_time(task: Task, unit: TimeUnit):
        if not task.forecast or not task.forecast.estimation_time:
            return 0
        delta = task.forecast.estimation_time.convert(unit).time_delta
        return delta if delta > 0 else 0

    def _calculate_sequential_dates(self, task: Task, current_start: datetime,
                                    parameters: ForecastGenerationParameters) -> datetime:
        if not task.forecast or not task.forecast.estimation_time:
            return current_start

        if task.child_tasks:
            child_start = current_start
            for child_task in task.child_tasks:
                if child_task.forecast:
                    child_start = self._calculate_sequential_dates(child_task, child_start, parameters)

            task.forecast.start_date = current_start

            if child_start > current_start:
                task.forecast.end_date = child_start
            else:
                duration_days = self._convert_estimation_time_into_duration_in_days(task.forecast.estimation_time,
                                                                                    parameters.velocity_strategy)
                task.forecast.end_date = current_start + timedelta(days=duration_days)

            return task.forecast.end_date
        else:
            task.forecast.start_date = current_start
            duration_days = self._convert_estimation_time_into_duration_in_days(task.forecast.estimation_time,
                                                                                parameters.velocity_strategy)
            task.forecast.end_date = current_start + timedelta(days=duration_days)
            return task.forecast.end_date

    def _convert_estimation_time_into_duration_in_days(self, estimation_time, velocity_strategy):
        if velocity_strategy == VelocityStrategy.IDEAL_VELOCITY:
            policy = self._ideal_time_policy
        else:
            policy = TimePolicy.ALL_HOURS

        return estimation_time.convert(TimeUnit.DAY, policy).time_delta

    @staticmethod
    def _create_total_spent_time(task: Task) -> Optional[Duration]:
        if not task.time_tracking or not task.time_tracking.total_spent_time:
            return None

        return task.time_tracking.total_spent_time

    async def _get_tasks(self, parameters: ForecastGenerationParameters, task_ids: list[str]) -> list[Task]:
        if StoryPointsStrategy.DIRECT == parameters.story_points_strategy:
            return await self._task_repository.get_tasks(task_ids)
        elif StoryPointsStrategy.CUMULATIVE == parameters.story_points_strategy:
            return await self._task_repository.get_tasks_with_full_hierarchy(task_ids)

        return []
