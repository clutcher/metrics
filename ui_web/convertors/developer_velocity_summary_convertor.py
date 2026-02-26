from typing import List, cast

from ..data.hierarchical_item_data import HierarchicalItemData
from ..data.velocity_task_detail_data import TaskVelocityData, DeveloperVelocitySummary


class DeveloperVelocitySummaryConvertor:

    def __init__(self, ideal_hours_per_day: float):
        self._ideal_hours_per_day = ideal_hours_per_day

    def enrich_with_summaries(self, groups: List[HierarchicalItemData]) -> List[HierarchicalItemData]:
        for group in groups:
            group.summary = DeveloperVelocitySummaryConvertor._calculate_summary(
                cast(List[TaskVelocityData], group.items), self._ideal_hours_per_day
            )
        return groups

    @staticmethod
    def _calculate_summary(tasks: List[TaskVelocityData],
                            ideal_hours_per_day: float) -> DeveloperVelocitySummary:
        total_sp = sum(t.developer_story_points for t in tasks)
        total_hours = sum(t.developer_time_hours for t in tasks)
        velocity = total_sp / (total_hours / ideal_hours_per_day) if total_hours > 0 else None
        return DeveloperVelocitySummary(
            total_story_points=total_sp,
            total_time_hours=total_hours,
            velocity=velocity
        )
