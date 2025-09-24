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


    @staticmethod
    async def populate_ideal_forecasts_batch(tasks: list[Task], forecast_api) -> None:
        if not tasks:
            return

        assignee_groups = await ForecastPopulationUtils._group_tasks_by_assignee(tasks)

        for assignee_id, assignee_tasks in assignee_groups.items():
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

            await forecast_api.generate_forecasts_for_tasks(assignee_tasks, parameters)

    @staticmethod
    async def _group_tasks_by_assignee(tasks: list[Task]) -> dict[str, list[Task]]:
        assignee_groups = {}
        tasks_without_assignees = 0

        for task in tasks:
            if not task.assignment or not task.assignment.assignee or not task.assignment.assignee.id:
                tasks_without_assignees += 1
                continue

            assignee_id = task.assignment.assignee.id
            if assignee_id not in assignee_groups:
                assignee_groups[assignee_id] = []
            assignee_groups[assignee_id].append(task)
        return assignee_groups
