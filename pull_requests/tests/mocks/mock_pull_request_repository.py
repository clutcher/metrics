from typing import List

from pull_requests.app.domain.model.pull_request import PullRequest, PullRequestRef, PullRequestSearchCriteria
from pull_requests.app.domain.model.review import ReviewInputs
from pull_requests.app.spi.pull_request_repository import PullRequestRepository


class MockPullRequestRepository(PullRequestRepository):

    def __init__(self, pull_requests: List[PullRequest] = None, review_inputs: ReviewInputs = None):
        self._pull_requests = pull_requests or []
        self._review_inputs = review_inputs or ReviewInputs()

    async def find_all(self, criteria: PullRequestSearchCriteria) -> List[PullRequest]:
        return self._pull_requests

    async def fetch_review_inputs(self, ref: PullRequestRef) -> ReviewInputs:
        return self._review_inputs
