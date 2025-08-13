from datetime import datetime
from typing import Optional, List

from django.conf import settings
from sd_metrics_lib.utils.time import TimeUnit

from forecast.app.domain.model.enums import VelocityStrategy, StoryPointsStrategy, SubjectType
from forecast.app.domain.model.forecast import Subject, ForecastGenerationParameters
from ..convertors.task_convertor import TaskConvertor
from ..convertors.task_forecast_chart_convertor import TaskForecastChartConvertor
from ..convertors.task_forecast_convertor import TaskForecastConvertor
from ..data.chart_data import ChartData
from ..data.task_data import TaskData
from ..data.task_forecast_data import TaskForecastRequestData, TaskForecastParamsData, TaskForecastSummaryData
from ..utils.task_forecast_chart_utils import TaskForecastChartUtils


class TaskForecastFacade:
    def __init__(self, forecast_api, task_forecast_convertor: TaskForecastConvertor,
                 task_convertor: TaskConvertor,
                 task_forecast_chart_convertor: TaskForecastChartConvertor):
        self.forecast_api = forecast_api
        self.task_forecast_convertor = task_forecast_convertor
        self.task_convertor = task_convertor
        self.task_forecast_chart_convertor = task_forecast_chart_convertor

    @staticmethod
    async def get_forecast_params_data(request_data: TaskForecastRequestData) -> TaskForecastParamsData:
        return TaskForecastParamsData(
            task_id=request_data.task_id,
            start_date=request_data.start_date,
            member_group=request_data.member_group,
            time_unit='day'
        )

    async def get_task_forecast_hierarchy_data(self, request_data: TaskForecastRequestData) -> List[TaskData]:
        task_id = request_data.task_id
        root_task = await self._calculate_task_forecast(task_id, request_data.member_group, request_data.start_date)

        if not root_task:
            return []

        task_data = self.task_convertor.convert_task_to_data(root_task)
        return [task_data]

    @staticmethod
    def get_forecast_summary_from_data(task_data_list: List[TaskData]) -> Optional[TaskForecastSummaryData]:
        if not task_data_list:
            return None

        total_days = 0.0
        start_dates = []
        end_dates = []
        task_forecasts = []
        first_task_velocity = None

        for task_data in task_data_list:
            if task_data.forecast and task_data.forecast.estimation_time_days:
                total_days += task_data.forecast.estimation_time_days

            if task_data.forecast and task_data.forecast.start_date:
                try:
                    start_date = datetime.fromisoformat(task_data.forecast.start_date.replace('Z', '+00:00'))
                    start_dates.append(start_date)
                except:
                    pass
            if task_data.forecast and task_data.forecast.end_date:
                try:
                    end_date = datetime.fromisoformat(task_data.forecast.end_date.replace('Z', '+00:00'))
                    end_dates.append(end_date)
                except:
                    pass
            if not first_task_velocity and task_data.forecast and task_data.forecast.velocity:
                first_task_velocity = task_data.forecast.velocity

            task_forecasts.extend(TaskForecastChartUtils.flatten_task_data_hierarchy_for_table(task_data))

        forecasted_start_date = min(start_dates) if start_dates else datetime.now()
        forecasted_end_date = max(end_dates) if end_dates else None

        return TaskForecastSummaryData(
            task_title="SUMMARY",
            total_estimation_days=total_days,
            forecasted_start_date=forecasted_start_date,
            forecasted_end_date=forecasted_end_date,
            average_team_velocity=first_task_velocity,
            task_forecasts=task_forecasts
        )

    def get_forecast_chart_from_data(self, task_data_list: List[TaskData]) -> Optional[ChartData]:
        return self.task_forecast_chart_convertor.convert_task_data_list_to_chart(task_data_list)

    async def _calculate_task_forecast(self, task_id: str, member_group: Optional[str],
                                       start_date: Optional[str] = None):
        subject = Subject(
            type=SubjectType.MEMBER_GROUP,
            id=member_group or "default"
        )

        forecast_start_date = datetime.now()
        if start_date:
            try:
                forecast_start_date = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                forecast_start_date = datetime.now()

        parameters = ForecastGenerationParameters(
            velocity_strategy=VelocityStrategy.REAL_VELOCITY,
            story_points_strategy=StoryPointsStrategy.CUMULATIVE,
            subject=subject,
            time_unit=TimeUnit[settings.METRICS_DEFAULT_VELOCITY_TIME_UNIT],
            start_date=forecast_start_date
        )

        tasks = await self.forecast_api.generate_forecasts_for_task_ids([task_id], parameters)

        if not tasks:
            return None

        return tasks[0]
