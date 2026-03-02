from typing import Dict, List, Optional

from sd_metrics_lib.calculators.story_points import ProportionalStoryPointCalculator
from sd_metrics_lib.utils.time import Duration, TimeUnit, TimePolicy

from tasks.app.domain.model.task import Task
from ..data.task_data import AssigneeData, AssignmentData, TimeTrackingData, SystemMetadataData
from ..data.velocity_task_detail_data import TaskVelocityData


class VelocityTaskDetailConvertor:

    def __init__(self, time_policy: TimePolicy):
        self._time_policy = time_policy

    def convert_tasks_to_developers_breakdown(self, tasks: List[Task],
                                              developer_names: List[str],
                                              developer_velocities: Dict[str, Optional[float]]) -> List[TaskVelocityData]:
        result = []
        for task in tasks:
            if not task.story_points or task.story_points <= 0:
                continue
            if not task.time_tracking or not task.time_tracking.spent_time_by_assignee:
                continue
            for developer_name in developer_names:
                if developer_name in task.time_tracking.spent_time_by_assignee:
                    velocity = developer_velocities.get(developer_name)
                    result.append(self._convert_task_for_developer(task, developer_name, velocity))
        return result

    def _convert_task_for_developer(self, task: Task, developer_name: str,
                                    velocity: Optional[float]) -> TaskVelocityData:
        developer_story_points = VelocityTaskDetailConvertor._calculate_developer_story_points(task, developer_name)
        developer_time_days = self._calculate_developer_time_days(task, developer_name)
        total_estimated_days = VelocityTaskDetailConvertor._calculate_estimated_days(task.story_points, velocity)
        estimated_days = VelocityTaskDetailConvertor._calculate_estimated_days(developer_story_points, velocity)
        deviation_percent = VelocityTaskDetailConvertor._calculate_deviation_percent(estimated_days, developer_time_days)

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
            developer_time_days=developer_time_days,
            total_estimated_days=total_estimated_days,
            estimated_days=estimated_days,
            deviation_percent=deviation_percent
        )

    @staticmethod
    def _calculate_estimated_days(story_points: float, velocity: Optional[float]) -> Optional[float]:
        if velocity is None or velocity <= 0 or story_points <= 0:
            return None
        return story_points / velocity

    @staticmethod
    def _calculate_deviation_percent(estimated_days: Optional[float],
                                     actual_days: float) -> Optional[float]:
        if estimated_days is None or estimated_days <= 0:
            return None
        return ((estimated_days - actual_days) / estimated_days) * 100

    @staticmethod
    def _calculate_developer_story_points(task: Task, developer_name: str) -> float:
        spent_time_by_assignee = task.time_tracking.spent_time_by_assignee
        developer_duration = spent_time_by_assignee[developer_name]
        total_duration = Duration.sum(spent_time_by_assignee.values(), unit=TimeUnit.SECOND)

        return ProportionalStoryPointCalculator.calculate(
            task.story_points, developer_duration, total_duration
        ) or 0.0

    def _calculate_developer_time_days(self, task: Task, developer_name: str) -> float:
        developer_duration = task.time_tracking.spent_time_by_assignee[developer_name]
        return developer_duration.convert(TimeUnit.DAY, self._time_policy).time_delta

    @staticmethod
    def _extract_system_metadata(task: Task) -> SystemMetadataData:
        if not task.system_metadata:
            return SystemMetadataData(original_status="")

        return SystemMetadataData(
            original_status=task.system_metadata.original_status,
            url=task.system_metadata.url
        )
