from datetime import datetime

from pull_requests.app.domain.model.pull_request import (
    Approval, ApprovalVote, Reviewer, ReviewTier
)
from pull_requests.app.domain.model.review import (
    PolicyEvaluationStatus, RawPolicyEvaluation, ReviewInputs, VoteEvent
)
from pull_requests.app.domain.pull_request_search_service import PullRequestSearchService
from pull_requests.app.domain.review.policy_gateway_evaluator import PolicyGatewayEvaluator
from pull_requests.app.domain.review.pull_request_review_enricher import PullRequestReviewEnricher
from pull_requests.app.domain.review.reset_approval_detector import ResetApprovalDetector
from pull_requests.app.domain.review.review_gate_evaluator import ReviewGateEvaluator
from pull_requests.app.domain.review.reviewer_seniority import ReviewerSeniority
from pull_requests.tests.mocks.mock_pull_request_repository import MockPullRequestRepository


def approval(tier: ReviewTier, vote: ApprovalVote = ApprovalVote.APPROVED,
             reviewer_id: str = None, name: str = "Reviewer", is_required: bool = False) -> Approval:
    identifier = reviewer_id or f"{name}-{tier.value}"
    return Approval(
        reviewer=Reviewer(id=identifier, display_name=name, tier=tier, is_required=is_required),
        vote=vote
    )


def reviewer_vote(reviewer_id: str, vote: ApprovalVote, name: str = "Reviewer") -> Approval:
    return Approval(reviewer=Reviewer(id=reviewer_id, display_name=name), vote=vote)


def vote_event(reviewer_id: str, vote: ApprovalVote, day: int, name: str = "Reviewer") -> VoteEvent:
    return VoteEvent(
        reviewer_id=reviewer_id, display_name=name, vote=vote, occurred_at=datetime(2026, 6, day)
    )


_POLICY_TYPE_IDS = {
    "build": "0609b952-1397-4640-95ec-e00a01b2c241",
    "reviewers": "fa4e907d-c16b-4a4c-9dfa-4906e5d171dd",
    "required": "fd2167ab-b0be-447a-8ec8-39368250530e",
    "comments": "c6a1889d-b943-4856-b76f-9e46bb6b0df2",
}


def policy_evaluation(policy_kind: str, status: PolicyEvaluationStatus, name: str = None,
                      is_expired: bool = False) -> RawPolicyEvaluation:
    return RawPolicyEvaluation(
        type_id=_POLICY_TYPE_IDS.get(policy_kind, policy_kind),
        display_name=name or policy_kind.capitalize(),
        status=status,
        is_expired=is_expired
    )


def detail_search_service(review_inputs: ReviewInputs) -> PullRequestSearchService:
    review_enricher = PullRequestReviewEnricher(
        reviewer_seniority=ReviewerSeniority(members={}, main_reviewer_levels=["lead", "arch"], seniority_levels={}),
        review_gate_evaluator=ReviewGateEvaluator(min_developer_approvals=2),
        reset_approval_detector=ResetApprovalDetector(),
        policy_gateway_evaluator=PolicyGatewayEvaluator()
    )
    return PullRequestSearchService(
        repository=MockPullRequestRepository(review_inputs=review_inputs),
        review_enricher=review_enricher
    )
