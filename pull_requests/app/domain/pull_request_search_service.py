from typing import List, Optional

from ..api.api_for_pull_request_search import ApiForPullRequestSearch
from ..spi.pull_request_repository import PullRequestRepository
from .model.pull_request import (
    PullRequest, PullRequestProjection, PullRequestRef, PullRequestSearchCriteria, ReviewState
)
from .review.pull_request_review_enricher import PullRequestReviewEnricher


class PullRequestSearchService(ApiForPullRequestSearch):

    def __init__(self, repository: PullRequestRepository, review_enricher: PullRequestReviewEnricher):
        self._repository = repository
        self._review_enricher = review_enricher

    async def search(self, criteria: Optional[PullRequestSearchCriteria] = None,
                     projection: PullRequestProjection = PullRequestProjection.SUMMARY) -> List[PullRequest]:
        search_criteria = criteria or PullRequestSearchCriteria()
        if projection is PullRequestProjection.REVIEW_DETAILS:
            return await self._search_review_details(search_criteria.target)
        return await self._search_summary(search_criteria)

    async def _search_summary(self, criteria: PullRequestSearchCriteria) -> List[PullRequest]:
        pull_requests = await self._repository.find_all(criteria)
        for pull_request in pull_requests:
            self._review_enricher.enrich_summary(pull_request)
        return pull_requests

    async def _search_review_details(self, target: PullRequestRef) -> List[PullRequest]:
        review_inputs = await self._repository.fetch_review_inputs(target)
        pull_request = PullRequest(
            id=target.pull_request_id,
            review=ReviewState(approvals=review_inputs.current_approvals)
        )
        self._review_enricher.enrich_details(pull_request, review_inputs)
        return [pull_request]
