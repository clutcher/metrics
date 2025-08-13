from typing import Dict

from sd_metrics_lib.sources.story_points import FunctionStoryPointExtractor
from sd_metrics_lib.sources.worklog import FunctionWorklogExtractor, FunctionTotalSpentTimeExtractor
from sd_metrics_lib.utils.time import Duration

from velocity.app.domain.model.task import Task


def extract_story_points(task: Task) -> float:
    return float(task.story_points) if task.story_points is not None else 0.0


def extract_worklog_by_assignee(task: Task) -> Dict[str, Duration]:
    if task.time_tracking and task.time_tracking.spent_time_by_assignee:
        return task.time_tracking.spent_time_by_assignee
    return {}


def extract_total_spent_time(task: Task) -> Duration:
    if task.time_tracking and task.time_tracking.total_spent_time:
        return task.time_tracking.total_spent_time
    return Duration.zero()


TaskModuleStoryPointExtractor = FunctionStoryPointExtractor(extract_story_points)
TaskModuleWorklogExtractor = FunctionWorklogExtractor(extract_worklog_by_assignee)
TaskModuleTotalSpentTimeExtractor = FunctionTotalSpentTimeExtractor(extract_total_spent_time)
