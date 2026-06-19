from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ApprovalVote(Enum):
    APPROVED = "approved"
    APPROVED_WITH_SUGGESTIONS = "approved_with_suggestions"
    WAITING = "waiting"
    REJECTED = "rejected"
    NO_VOTE = "no_vote"

    @property
    def is_positive(self) -> bool:
        return self in (ApprovalVote.APPROVED, ApprovalVote.APPROVED_WITH_SUGGESTIONS)

    @property
    def is_rejection(self) -> bool:
        return self is ApprovalVote.REJECTED


class ReviewTier(Enum):
    MAIN = "main"
    ADDITIONAL = "additional"


class GatewayState(Enum):
    READY = "ready"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"


class GatewayBlocker(Enum):
    CI = "CI"
    CHANGES_REQUESTED = "Changes requested"
    MERGE_CONFLICT = "Merge conflict"


@dataclass(slots=True)
class Reviewer:
    id: str
    display_name: str
    tier: ReviewTier = ReviewTier.ADDITIONAL
    level: Optional[str] = None
    is_required: bool = False


@dataclass(slots=True)
class Approval:
    reviewer: Reviewer
    vote: ApprovalVote


@dataclass(slots=True)
class Author:
    id: str
    display_name: str


@dataclass(slots=True)
class GatewayResult:
    state: GatewayState
    blockers: List[GatewayBlocker] = field(default_factory=list)


@dataclass(slots=True)
class ReviewState:
    approvals: List[Approval] = field(default_factory=list)
    reset_approvals: List[Approval] = field(default_factory=list)
    gateway: Optional[GatewayResult] = None
    internal_gate_met: bool = False


@dataclass(slots=True)
class PullRequest:
    id: str
    title: str = ""
    author: Optional[Author] = None
    status: str = ""
    url: Optional[str] = None
    repository: Optional[str] = None
    repository_id: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    source_branch: Optional[str] = None
    is_draft: bool = False
    created_date: Optional[datetime] = None
    linked_task_id: Optional[str] = None
    review: ReviewState = field(default_factory=ReviewState)


@dataclass(slots=True)
class PullRequestRef:
    pull_request_id: str
    repository_id: str
    project_id: str
    project_name: str


class PullRequestProjection(Enum):
    SUMMARY = "summary"
    REVIEW_DETAILS = "review_details"


@dataclass(slots=True)
class PullRequestSearchCriteria:
    status_filter: str = "active"
    target: Optional[PullRequestRef] = None
