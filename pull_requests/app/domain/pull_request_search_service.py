from typing import List, Optional

from ..api.api_for_pull_request_search import ApiForPullRequestSearch
from ..spi.pull_request_repository import PullRequestRepository
from .model.pull_request import PullRequest, PullRequestSearchCriteria
from .review.review_gate_evaluator import ReviewGateEvaluator
from .review.reviewer_seniority import ReviewerSeniority


class PullRequestSearchService(ApiForPullRequestSearch):

    def __init__(self, repository: PullRequestRepository, reviewer_seniority: ReviewerSeniority,
                 review_gate_evaluator: ReviewGateEvaluator):
        self._repository = repository
        self._reviewer_seniority = reviewer_seniority
        self._review_gate_evaluator = review_gate_evaluator

    async def search(self, criteria: Optional[PullRequestSearchCriteria] = None) -> List[PullRequest]:
        search_criteria = criteria or PullRequestSearchCriteria()
        pull_requests = await self._repository.find_all(search_criteria)
        for pull_request in pull_requests:
            self._enrich_with_review_state(pull_request)
        return pull_requests

    def _enrich_with_review_state(self, pull_request: PullRequest) -> None:
        self._assign_reviewer_tiers(pull_request)
        pull_request.approvals.sort(key=lambda approval: self._reviewer_seniority.approval_sort_key(approval.reviewer))
        pull_request.internal_gate_met = self._review_gate_evaluator.evaluate_internal_gate(pull_request.approvals)
        pull_request.required_gate_met = self._review_gate_evaluator.evaluate_required_gate(pull_request.approvals)

    def _assign_reviewer_tiers(self, pull_request: PullRequest) -> None:
        for approval in pull_request.approvals:
            reviewer = approval.reviewer
            reviewer.level = self._reviewer_seniority.resolve_level(reviewer.display_name)
            reviewer.tier = self._reviewer_seniority.resolve_tier(reviewer.display_name)
