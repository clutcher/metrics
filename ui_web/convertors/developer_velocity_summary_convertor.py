from typing import List, Optional, cast

from ..data.hierarchical_item_data import HierarchicalItemData
from ..data.velocity_task_detail_data import TaskVelocityData, DeveloperVelocitySummary


class DeveloperVelocitySummaryConvertor:

    def __init__(self, working_days_per_month: int):
        self._working_days_per_month = working_days_per_month

    def enrich_with_summaries(self, groups: List[HierarchicalItemData]) -> List[HierarchicalItemData]:
        for group in groups:
            group.summary = self._calculate_summary(cast(List[TaskVelocityData], group.items))
        return groups

    def _calculate_summary(self, tasks: List[TaskVelocityData]) -> DeveloperVelocitySummary:
        total_sp = sum(t.developer_story_points for t in tasks)
        total_days = sum(t.developer_time_days for t in tasks)
        velocity = total_sp / total_days if total_days > 0 else None

        total_task_sp = DeveloperVelocitySummaryConvertor._sum_task_story_points(tasks)
        total_estimated_days = DeveloperVelocitySummaryConvertor._sum_estimated_days(tasks)
        average_deviation_percent = DeveloperVelocitySummaryConvertor._average_deviation_percent(tasks)
        workload_percent = self._calculate_workload_percent(total_days)

        return DeveloperVelocitySummary(
            total_story_points=total_sp,
            total_time_days=total_days,
            velocity=velocity,
            total_task_story_points=total_task_sp,
            total_estimated_days=total_estimated_days,
            average_deviation_percent=average_deviation_percent,
            working_days=total_days,
            working_days_in_month=self._working_days_per_month,
            workload_percent=workload_percent
        )

    @staticmethod
    def _sum_task_story_points(tasks: List[TaskVelocityData]) -> Optional[float]:
        tasks_with_sp = [t for t in tasks if t.story_points is not None]
        if not tasks_with_sp:
            return None
        return sum(t.story_points for t in tasks_with_sp)

    @staticmethod
    def _sum_estimated_days(tasks: List[TaskVelocityData]) -> Optional[float]:
        tasks_with_estimation = [t for t in tasks if t.estimated_days is not None]
        if not tasks_with_estimation:
            return None
        return sum(t.estimated_days for t in tasks_with_estimation)

    @staticmethod
    def _average_deviation_percent(tasks: List[TaskVelocityData]) -> Optional[float]:
        tasks_with_deviation = [t for t in tasks if t.deviation_percent is not None]
        if not tasks_with_deviation:
            return None
        return sum(t.deviation_percent for t in tasks_with_deviation) / len(tasks_with_deviation)

    def _calculate_workload_percent(self, working_days: float) -> Optional[float]:
        if self._working_days_per_month <= 0:
            return None
        return (working_days / self._working_days_per_month) * 100
