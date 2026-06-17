from abc import ABC, abstractmethod
from typing import List

from ..domain.model.pull_request import PullRequest, PullRequestSearchCriteria


class PullRequestRepository(ABC):

    @abstractmethod
    async def find_all(self, criteria: PullRequestSearchCriteria) -> List[PullRequest]:
        pass
