from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from .pull_request import Approval, ApprovalVote


class PolicyEvaluationStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_APPLICABLE = "notApplicable"
    BROKEN = "broken"


class PolicyCategory(Enum):
    BUILD = "build"
    REVIEWERS = "reviewers"
    COMMENTS = "comments"
    WORK_ITEM = "work_item"
    STATUS = "status"
    OTHER = "other"


@dataclass(slots=True)
class VoteEvent:
    reviewer_id: str
    display_name: str
    vote: ApprovalVote
    occurred_at: datetime


@dataclass(slots=True)
class RawPolicyEvaluation:
    type_id: str
    display_name: str
    status: PolicyEvaluationStatus
    is_expired: bool = False
    category: Optional["PolicyCategory"] = None


@dataclass(slots=True)
class ReviewInputs:
    current_approvals: List[Approval] = field(default_factory=list)
    vote_events: List[VoteEvent] = field(default_factory=list)
    policy_evaluations: List[RawPolicyEvaluation] = field(default_factory=list)
    has_merge_conflict: bool = False
