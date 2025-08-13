from typing import List, Union, TYPE_CHECKING

from sd_metrics_lib.utils.time import TimeUnit, TimePolicy, Duration

from ..data.task_data import TaskData

if TYPE_CHECKING:
    from tasks.app.domain.model.task import Task


class TaskSortUtils:

    @staticmethod
    def sort_tasks_by_spent_time(tasks: List[Union[TaskData, 'Task']]) -> List[Union[TaskData, 'Task']]:
        return sorted(tasks, key=lambda task: -TaskSortUtils._extract_task_spent_time_seconds(task))

    @staticmethod
    def _extract_task_spent_time_seconds(task: Union[TaskData, 'Task']) -> float:
        if not task.time_tracking:
            return 0.0

        if hasattr(task.time_tracking, 'total_spent_time_days'):
            total_spent_time_days = task.time_tracking.total_spent_time_days
            if not total_spent_time_days:
                return 0.0
            return Duration.of(total_spent_time_days, TimeUnit.DAY).convert(TimeUnit.SECOND, TimePolicy.BUSINESS_HOURS).time_delta
        elif hasattr(task.time_tracking, 'total_spent_time'):
            total_spent_time = task.time_tracking.total_spent_time
            if not total_spent_time:
                return 0.0
            return total_spent_time.convert(TimeUnit.SECOND, TimePolicy.BUSINESS_HOURS).time_delta

        return 0.0