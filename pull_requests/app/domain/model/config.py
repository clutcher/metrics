from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class AzureRepoConfig:
    organization_url: Optional[str]
    pat: Optional[str]
    project_keys: List[str]


@dataclass(slots=True)
class BitbucketConfig:
    url: Optional[str]
    workspace: Optional[str]
    username: Optional[str]
    app_password: Optional[str]
    repositories: List[str]


@dataclass(slots=True)
class ReviewGateConfig:
    main_reviewer_levels: List[str]
    min_developer_approvals: int


@dataclass(slots=True)
class PullRequestsConfig:
    task_tracker: str
    azure: AzureRepoConfig
    bitbucket: BitbucketConfig
    members: Dict[str, Dict[str, Any]]
    seniority_levels: Dict[str, float]
    review_gate: ReviewGateConfig

    def is_azure_tracker(self) -> bool:
        return self.task_tracker == 'azure'

    def is_jira_tracker(self) -> bool:
        return self.task_tracker == 'jira'

    def is_azure_configured(self) -> bool:
        return bool(self.azure.organization_url and self.azure.pat and self.azure.project_keys)

    def is_bitbucket_configured(self) -> bool:
        return bool(self.bitbucket.username and self.bitbucket.app_password and self.bitbucket.repositories)
