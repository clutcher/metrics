from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass(slots=True)
class JiraConfig:
    jira_server_url: Optional[str]
    jira_email: Optional[str]
    jira_api_token: Optional[str]
    story_point_custom_field_id: str

@dataclass(slots=True)
class AzureConfig:
    azure_organization_url: Optional[str]
    azure_pat: Optional[str]

@dataclass(slots=True)
class ProjectConfig:
    project_keys: List[str]
    task_tracker: str

@dataclass(slots=True)
class WorkflowConfig:
    stages: Dict[str, List[str]]
    in_progress_status_codes: List[str]
    pending_status_codes: List[str]
    done_status_codes: List[str]
    recently_finished_tasks_days: int

@dataclass(slots=True)
class TaskFilterConfig:
    global_task_types_filter: List[str]
    global_team_filter: Optional[List[str]]

@dataclass(slots=True)
class MemberGroupConfig:
    members: Dict[str, Dict[str, Any]]
    default_member_group_when_missing: Optional[str]
    
    def get_available_member_groups(self) -> Dict[str, str]:
        member_groups = {}
        for member_data in self.members.values():
            member_groups_of_member = member_data.get('member_groups', [])
            for member_group_name in member_groups_of_member:
                member_groups[member_group_name] = member_group_name

        if self.default_member_group_when_missing:
            member_groups[self.default_member_group_when_missing] = self.default_member_group_when_missing
        
        return member_groups

@dataclass(slots=True)
class EstimationConfig:
    working_days_per_month: int
    default_story_points_value_when_missing: float
    ideal_hours_per_day: float
    story_points_to_ideal_hours_convertion_ratio: float
    default_seniority_level_when_missing: str
    default_health_status_when_missing: str

@dataclass(slots=True)
class TasksConfig:
    jira: JiraConfig
    azure: AzureConfig
    project: ProjectConfig
    workflow: WorkflowConfig
    task_filter: TaskFilterConfig
    member_group: MemberGroupConfig
    estimation: EstimationConfig
    
    def get_available_member_group_ids(self) -> List[str]:
        return sorted(self.member_group.get_available_member_groups().keys())
    
    def get_assignee_member_groups(self, assignee_id: str) -> List[str]:
        member_data = self.member_group.members.get(assignee_id, {})
        return member_data.get('member_groups', [])
    
    def get_assignee_level(self, assignee_id: str) -> Optional[str]:
        member_data = self.member_group.members.get(assignee_id, {})
        return member_data.get('level')
    
    def get_assignee_stages(self, assignee_id: str) -> List[str]:
        member_data = self.member_group.members.get(assignee_id, {})
        return member_data.get('stages', [])
