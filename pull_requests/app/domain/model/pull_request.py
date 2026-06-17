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
class PullRequest:
    id: str
    title: str
    author: Author
    status: str
    url: Optional[str] = None
    repository: Optional[str] = None
    source_branch: Optional[str] = None
    is_draft: bool = False
    created_date: Optional[datetime] = None
    approvals: List[Approval] = field(default_factory=list)
    linked_task_id: Optional[str] = None
    internal_gate_met: bool = False
    required_gate_met: Optional[bool] = None


@dataclass(slots=True)
class PullRequestSearchCriteria:
    status_filter: str = "active"
