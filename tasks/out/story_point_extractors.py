from typing import Optional, Dict, Any, Callable

from tasks.app.domain.model.config import TasksConfig


def extract_story_points(fields: Dict[str, Any], custom_field_id: Optional[str], 
                        default_field_id: str, default_value_when_missing: float) -> float:
    if custom_field_id:
        custom_field_value = fields.get(custom_field_id)
        if custom_field_value is not None:
            return float(custom_field_value)

    default_story_points = fields.get(default_field_id)
    if default_story_points is not None:
        return float(default_story_points)

    return default_value_when_missing


def extract_jira_story_points(config: TasksConfig) -> Callable[[dict], float]:
    return lambda jira_task: extract_story_points(
        fields=jira_task.get('fields', {}),
        custom_field_id=config.jira.story_point_custom_field_id,
        default_field_id='customfield_10016',
        default_value_when_missing=config.estimation.default_story_points_value_when_missing
    )


def extract_azure_story_points(config: TasksConfig) -> Callable[[Any], float]:
    return lambda azure_task: extract_story_points(
        fields=azure_task.fields,
        custom_field_id=config.jira.story_point_custom_field_id,
        default_field_id="Microsoft.VSTS.Scheduling.StoryPoints",
        default_value_when_missing=config.estimation.default_story_points_value_when_missing
    )


