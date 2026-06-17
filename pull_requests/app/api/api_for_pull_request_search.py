from abc import ABC, abstractmethod
from typing import List, Optional

from ..domain.model.pull_request import PullRequest, PullRequestSearchCriteria


class ApiForPullRequestSearch(ABC):

    @abstractmethod
    async def search(self, criteria: Optional[PullRequestSearchCriteria] = None) -> List[PullRequest]:
        pass
