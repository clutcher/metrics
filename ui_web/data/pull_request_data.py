from dataclasses import dataclass, field
from typing import List, Optional

from .task_data import ReleaseData


@dataclass(slots=True)
class ApprovalData:
    display_name: str
    state: str
    tier: str
    is_approval: bool


@dataclass(slots=True)
class PersonActivitySummaryData:
    display_name: str
    created_count: int = 0
    approved_count: int = 0
    changes_requested_count: int = 0


@dataclass(slots=True)
class LinkedTaskData:
    id: str
    url: Optional[str] = None
    status: Optional[str] = None
    iteration: Optional[str] = None
    releases: Optional[List[ReleaseData]] = None


@dataclass(slots=True)
class PolicyResultData:
    name: str
    status: str
    css_class: str
    icon: str


@dataclass(slots=True)
class PullRequestData:
    id: str
    title: str = ""
    author_name: str = ""
    status: str = ""
    internal_gate: bool = False
    url: Optional[str] = None
    repository: Optional[str] = None
    repository_id: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    is_draft: bool = False
    approvals: List[ApprovalData] = field(default_factory=list)
    policies: List[PolicyResultData] = field(default_factory=list)
    linked_task: Optional[LinkedTaskData] = None
