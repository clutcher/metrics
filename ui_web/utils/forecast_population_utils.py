from django.conf import settings
from sd_metrics_lib.utils.time import TimeUnit

from forecast.app.domain.model.enums import VelocityStrategy, StoryPointsStrategy, SubjectType
from forecast.app.domain.model.forecast import ForecastGenerationParameters, Subject
from tasks.app.domain.model.task import Task


class ForecastPopulationUtils:

    @staticmethod
    async def populate_ideal_forecast_for_task(task: Task, forecast_api) -> None:

        if not task.assignment or not task.assignment.assignee:
            return

        assignee_id = task.assignment.assignee.id
        if not assignee_id:
            return

        subject = Subject(
            type=SubjectType.MEMBER,
            id=assignee_id
        )

        parameters = ForecastGenerationParameters(
            velocity_strategy=VelocityStrategy.IDEAL_VELOCITY,
            story_points_strategy=StoryPointsStrategy.DIRECT,
            subject=subject,
            time_unit=TimeUnit[settings.METRICS_DEFAULT_VELOCITY_TIME_UNIT]
        )

        await forecast_api.generate_forecasts_for_tasks([task], parameters)