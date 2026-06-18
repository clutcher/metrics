from abc import ABC, abstractmethod
from typing import List

from ..domain.model.pull_request import PullRequest, PullRequestRef, PullRequestSearchCriteria
from ..domain.model.review import ReviewInputs


class PullRequestRepository(ABC):

    @abstractmethod
    async def find_all(self, criteria: PullRequestSearchCriteria) -> List[PullRequest]:
        pass

    @abstractmethod
    async def fetch_review_inputs(self, ref: PullRequestRef) -> ReviewInputs:
        pass
