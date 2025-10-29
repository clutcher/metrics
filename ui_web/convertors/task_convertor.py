from typing import Optional

from sd_metrics_lib.utils.time import Duration, TimeUnit, TimePolicy

from forecast.app.domain.model.forecast import Forecast
from tasks.app.domain.model.task import Task, Assignment, TimeTracking, SystemMetadata
from ..data.member_data import MemberGroupData
from ..data.task_data import (
    TaskData, AssigneeData, AssignmentData, TimeTrackingData, SystemMetadataData,
    ForecastData
)


class TaskConvertor:

    def __init__(self, time_policy: TimePolicy):
        self._time_policy = time_policy

    def convert_task_to_data(self, task: Task) -> TaskData:
        child_tasks_data = None
        if task.child_tasks:
            child_tasks_data = [self.convert_task_to_data(child_task) for child_task in task.child_tasks]

        return TaskData(
            id=task.id,
            title=task.title,
            assignment=self._convert_assignment_to_data(task.assignment),
            time_tracking=self._convert_time_tracking_to_data(task.time_tracking),
            system_metadata=self._convert_system_metadata_to_data(task.system_metadata),
            story_points=task.story_points,
            priority=task.priority,
            child_tasks_count=task.child_tasks_count or 0,
            stage=task.stage,
            forecast=self._convert_forecast_to_data(task.forecast) if task.forecast else None,
            child_tasks=child_tasks_data
        )

    @staticmethod
    def _convert_assignment_to_data(assignment: Assignment) -> AssignmentData:
        assignee_data = None
        if assignment and assignment.assignee:
            assignee_data = AssigneeData(
                id=assignment.assignee.id,
                display_name=assignment.assignee.display_name,
                avatar_url=assignment.assignee.avatar_url
            )

        member_group_data = None
        if assignment and assignment.member_group:
            member_group_data = MemberGroupData(
                id=assignment.member_group.id,
                name=assignment.member_group.name
            )

        return AssignmentData(
            assignee=assignee_data,
            member_group=member_group_data
        )

    def _convert_time_tracking_to_data(self, time_tracking: TimeTracking) -> TimeTrackingData:
        total_spent_time_days = None
        current_assignee_spent_time_days = None

        if time_tracking:
            if time_tracking.total_spent_time:
                total_spent_time_days = self._convert_duration_to_business_days(time_tracking.total_spent_time)

            if time_tracking.current_assignee_spent_time:
                current_assignee_spent_time_days = self._convert_duration_to_business_days(
                    time_tracking.current_assignee_spent_time)

        return TimeTrackingData(
            total_spent_time_days=total_spent_time_days,
            current_assignee_spent_time_days=current_assignee_spent_time_days
        )

    @staticmethod
    def _convert_system_metadata_to_data(system_metadata: SystemMetadata) -> SystemMetadataData:
        return SystemMetadataData(
            original_status=system_metadata.original_status,
            url=system_metadata.url
        )

    def _convert_forecast_to_data(self, forecast: Optional[Forecast]) -> Optional[ForecastData]:
        if not forecast:
            return None

        health_status = None
        estimation_time_days = None
        start_date = None
        end_date = None
        velocity = None

        if forecast.target and forecast.target.health_status:
            health_status = forecast.target.health_status

        if forecast.estimation_time:
            estimation_time_days = self._convert_duration_to_business_days(
                forecast.estimation_time,
                time_policy=self._time_policy
            )

        if forecast.start_date:
            start_date = forecast.start_date.isoformat()

        if forecast.end_date:
            end_date = forecast.end_date.isoformat()

        if forecast.velocity:
            velocity = forecast.velocity

        return ForecastData(
            health_status=health_status,
            estimation_time_days=estimation_time_days,
            start_date=start_date,
            end_date=end_date,
            velocity=velocity
        )

    def get_task_estimation_hours(self, task) -> float:
        if task.forecast and task.forecast.estimation_time:
            return task.forecast.estimation_time.convert(TimeUnit.HOUR, self._time_policy).time_delta
        return 0.0

    @staticmethod
    def _convert_duration_to_business_days(duration: Duration,
                                           time_policy: TimePolicy = TimePolicy.BUSINESS_HOURS) -> float:
        return duration.convert(TimeUnit.DAY, time_policy).time_delta
