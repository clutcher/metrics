from typing import List, Optional

from ..data.pull_request_data import PullRequestData


class PullRequestFilterUtils:

    @staticmethod
    def build_author_options(pull_requests: List[PullRequestData]) -> List[str]:
        return sorted({pull_request.author_name for pull_request in pull_requests}, key=str.lower)

    @staticmethod
    def filter_by_author(pull_requests: List[PullRequestData], author_name: Optional[str]) -> List[PullRequestData]:
        if not author_name:
            return pull_requests
        return [pull_request for pull_request in pull_requests if pull_request.author_name == author_name]
