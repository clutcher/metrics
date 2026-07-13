from ui_web.data.member_data import MemberGroupData
from ui_web.data.task_data import (
    AssigneeData, AssignmentData, ForecastData, ReleaseData, SystemMetadataData, TaskData, TimeTrackingData
)


def task_data(task_id="TASK-1", priority=None, assignee_id=None, member_group=None, releases=None,
              parent_id=None, parent_title="", stage=None, status="In Progress", story_points=None,
              health=None, iteration=None):
    assignee = AssigneeData(id=assignee_id, display_name=assignee_id) if assignee_id else None
    group = MemberGroupData(id=member_group, name=member_group) if member_group else None
    release_data = [ReleaseData(id=release_id, name=name) for release_id, name in releases] if releases else None
    parent = TaskData(
        id=parent_id,
        title=parent_title,
        assignment=AssignmentData(),
        time_tracking=TimeTrackingData(),
        system_metadata=SystemMetadataData(original_status="")
    ) if parent_id else None
    forecast = ForecastData(health_status=health) if health else None
    return TaskData(
        id=task_id,
        title=f"Task {task_id}",
        assignment=AssignmentData(assignee=assignee, member_group=group),
        time_tracking=TimeTrackingData(),
        system_metadata=SystemMetadataData(original_status=status),
        priority=priority,
        releases=release_data,
        parent=parent,
        stage=stage,
        iteration=iteration,
        story_points=story_points,
        forecast=forecast
    )
