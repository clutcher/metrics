from django.conf import settings

from .app.domain.model.config import (
    TasksConfig, JiraConfig, AzureConfig, ProjectConfig, WorkflowConfig,
    TaskFilterConfig, MemberGroupConfig, EstimationConfig
)


def load_tasks_config() -> TasksConfig:
    jira = JiraConfig(
        jira_server_url=settings.METRICS_JIRA_SERVER_URL,
        jira_email=settings.METRICS_JIRA_EMAIL,
        jira_api_token=settings.METRICS_JIRA_API_TOKEN,
        story_point_custom_field_id=settings.METRICS_STORY_POINT_CUSTOM_FIELD_ID
    )
    
    azure = AzureConfig(
        azure_organization_url=settings.METRICS_AZURE_ORGANIZATION_URL,
        azure_pat=settings.METRICS_AZURE_PAT
    )
    
    project = ProjectConfig(
        project_keys=settings.METRICS_PROJECT_KEYS,
        task_tracker=settings.METRICS_TASK_TRACKER
    )
    
    workflow = WorkflowConfig(
        stages=settings.METRICS_STAGES,
        in_progress_status_codes=settings.METRICS_IN_PROGRESS_STATUS_CODES,
        pending_status_codes=settings.METRICS_PENDING_STATUS_CODES,
        done_status_codes=settings.METRICS_DONE_STATUS_CODES,
        recently_finished_tasks_days=settings.METRICS_RECENTLY_FINISHED_TASKS_DAYS
    )
    
    task_filter = TaskFilterConfig(
        global_task_types_filter=settings.METRICS_GLOBAL_TASK_TYPES_FILTER,
        global_team_filter=settings.METRICS_GLOBAL_TEAM_FILTER
    )
    
    member_group = MemberGroupConfig(
        members=settings.METRICS_MEMBERS,
        default_member_group_when_missing=settings.METRICS_MEMBER_GROUP_WHEN_MISSING
    )

    estimation = EstimationConfig(
        working_days_per_month=settings.METRICS_WORKING_DAYS_PER_MONTH,
        default_story_points_value_when_missing=settings.METRICS_DEFAULT_STORY_POINTS_VALUE_WHEN_MISSING,
        ideal_hours_per_day=settings.METRICS_IDEAL_HOURS_PER_DAY,
        story_points_to_ideal_hours_convertion_ratio=settings.METRICS_STORY_POINTS_TO_IDEAL_HOURS_CONVERTION_RATIO,
        default_seniority_level_when_missing=settings.METRICS_DEFAULT_SENIORITY_LEVEL_WHEN_MISSING,
        default_health_status_when_missing=settings.METRICS_DEFAULT_HEALTH_STATUS_WHEN_MISSING
    )
    
    return TasksConfig(
        jira=jira,
        azure=azure,
        project=project,
        workflow=workflow,
        task_filter=task_filter,
        member_group=member_group,
        estimation=estimation
    )