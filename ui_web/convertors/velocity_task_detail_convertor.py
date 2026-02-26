from sd_metrics_lib.calculators.story_points import ProportionalStoryPointCalculator
from sd_metrics_lib.utils.time import Duration, TimeUnit, TimePolicy

from tasks.app.domain.model.task import Task
from ..data.task_data import AssigneeData, AssignmentData, TimeTrackingData, SystemMetadataData
from ..data.velocity_task_detail_data import TaskVelocityData


class VelocityTaskDetailConvertor:

    @staticmethod
    def convert_task_for_developer(task: Task, developer_name: str) -> TaskVelocityData:
        developer_story_points = VelocityTaskDetailConvertor._calculate_developer_story_points(task, developer_name)
        developer_time_hours = VelocityTaskDetailConvertor._calculate_developer_time_hours(task, developer_name)

        return TaskVelocityData(
            id=task.id,
            title=task.title,
            assignment=AssignmentData(
                assignee=AssigneeData(id=developer_name, display_name=developer_name)
            ),
            time_tracking=TimeTrackingData(),
            system_metadata=VelocityTaskDetailConvertor._extract_system_metadata(task),
            story_points=task.story_points,
            developer_story_points=developer_story_points,
            developer_time_hours=developer_time_hours
        )

    @staticmethod
    def _calculate_developer_story_points(task: Task, developer_name: str) -> float:
        spent_time_by_assignee = task.time_tracking.spent_time_by_assignee
        developer_duration = spent_time_by_assignee[developer_name]
        total_duration = Duration.sum(spent_time_by_assignee.values(), unit=TimeUnit.SECOND)

        return ProportionalStoryPointCalculator.calculate(
            task.story_points, developer_duration, total_duration
        ) or 0.0

    @staticmethod
    def _calculate_developer_time_hours(task: Task, developer_name: str) -> float:
        developer_duration = task.time_tracking.spent_time_by_assignee[developer_name]
        return developer_duration.convert(TimeUnit.HOUR, TimePolicy.BUSINESS_HOURS).time_delta

    @staticmethod
    def _extract_system_metadata(task: Task) -> SystemMetadataData:
        if not task.system_metadata:
            return SystemMetadataData(original_status="")

        return SystemMetadataData(
            original_status=task.system_metadata.original_status,
            url=task.system_metadata.url
        )
