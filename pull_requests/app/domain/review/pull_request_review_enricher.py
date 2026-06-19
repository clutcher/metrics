from typing import List

from ..model.pull_request import Approval, PullRequest
from ..model.review import ReviewInputs
from .policy_gateway_evaluator import PolicyGatewayEvaluator
from .reset_approval_detector import ResetApprovalDetector
from .review_gate_evaluator import ReviewGateEvaluator
from .reviewer_seniority import ReviewerSeniority


class PullRequestReviewEnricher:

    def __init__(self, reviewer_seniority: ReviewerSeniority,
                 review_gate_evaluator: ReviewGateEvaluator,
                 reset_approval_detector: ResetApprovalDetector,
                 policy_gateway_evaluator: PolicyGatewayEvaluator):
        self._reviewer_seniority = reviewer_seniority
        self._review_gate_evaluator = review_gate_evaluator
        self._reset_approval_detector = reset_approval_detector
        self._policy_gateway_evaluator = policy_gateway_evaluator

    def enrich_summary(self, pull_request: PullRequest) -> None:
        review = pull_request.review
        self._enrich_reviewers(review.approvals)
        review.internal_gate_met = self._review_gate_evaluator.evaluate_internal_gate(review.approvals)

    def enrich_details(self, pull_request: PullRequest, review_inputs: ReviewInputs) -> None:
        review = pull_request.review
        self._enrich_reviewers(review.approvals)
        review.reset_approvals = self._enrich_reviewers(
            self._reset_approval_detector.detect(review.approvals, review_inputs.vote_events)
        )
        review.gateway = self._policy_gateway_evaluator.evaluate(
            review_inputs.policy_evaluations, review.approvals, review_inputs.has_merge_conflict
        )

    def _enrich_reviewers(self, approvals: List[Approval]) -> List[Approval]:
        for approval in approvals:
            reviewer = approval.reviewer
            reviewer.level = self._reviewer_seniority.resolve_level(reviewer.display_name)
            reviewer.tier = self._reviewer_seniority.resolve_tier(reviewer.display_name)
        approvals.sort(key=lambda approval: self._reviewer_seniority.approval_sort_key(approval.reviewer))
        return approvals
