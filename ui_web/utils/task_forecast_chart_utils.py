from typing import List

from django.conf import settings

from ..data.task_data import TaskData
from ..data.task_forecast_data import TaskForecastBreakdownItem


class TaskForecastChartUtils:

    @staticmethod
    def flatten_task_data_hierarchy_for_table(task_data: TaskData, level: int = 0) -> List[TaskForecastBreakdownItem]:
        tasks = []
        estimation_days = 0.0
        if task_data.forecast and task_data.forecast.estimation_time_days:
            estimation_days = task_data.forecast.estimation_time_days
        
        active_children = []
        if task_data.child_tasks:
            for child in task_data.child_tasks:
                if TaskForecastChartUtils._is_task_data_active(child):
                    active_children.append(child)
        
        tasks.append(TaskForecastBreakdownItem(
            task_id=task_data.id,
            task_title=task_data.title,
            estimation_days=estimation_days,
            level=level,
            has_children=len(active_children) > 0
        ))
        
        for child in active_children:
            tasks.extend(TaskForecastChartUtils.flatten_task_data_hierarchy_for_table(child, level + 1))
        
        return tasks

    @staticmethod
    def _is_task_data_active(task_data: TaskData) -> bool:
        if not task_data.system_metadata or not task_data.system_metadata.original_status:
            return True
        
        task_status = task_data.system_metadata.original_status
        done_statuses = settings.METRICS_DONE_STATUS_CODES
        
        return task_status not in done_statuses