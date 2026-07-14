from typing import List, Optional, Tuple

from .natural_sort import NATURAL_KEY
from ..data.pull_request_data import PullRequestData
from ..data.task_data import ReleaseData


class PullRequestFilterUtils:

    @staticmethod
    def build_author_options(pull_requests: List[PullRequestData]) -> List[str]:
        return sorted({pull_request.author_name for pull_request in pull_requests}, key=str.lower)

    @staticmethod
    def filter_by_author(pull_requests: List[PullRequestData], author_name: Optional[str]) -> List[PullRequestData]:
        if not author_name:
            return pull_requests
        return [pull_request for pull_request in pull_requests if pull_request.author_name == author_name]

    @staticmethod
    def build_iteration_options(pull_requests: List[PullRequestData]) -> List[str]:
        iterations = set()
        for pull_request in pull_requests:
            iteration = PullRequestFilterUtils._iteration_of(pull_request)
            if iteration:
                iterations.add(iteration)
        return sorted(iterations, key=NATURAL_KEY)

    @staticmethod
    def filter_by_iteration(pull_requests: List[PullRequestData], iteration: Optional[str]) -> List[PullRequestData]:
        if not iteration:
            return pull_requests
        return [
            pull_request for pull_request in pull_requests
            if PullRequestFilterUtils._iteration_of(pull_request) == iteration
        ]

    @staticmethod
    def build_release_options(pull_requests: List[PullRequestData]) -> List[Tuple[str, str]]:
        labels_by_id = {}
        for pull_request in pull_requests:
            for release in PullRequestFilterUtils._releases_of(pull_request):
                labels_by_id.setdefault(release.id, release.name)
        return sorted(labels_by_id.items(), key=lambda pair: NATURAL_KEY(pair[1]))

    @staticmethod
    def filter_by_release(pull_requests: List[PullRequestData], release_id: Optional[str]) -> List[PullRequestData]:
        if not release_id:
            return pull_requests
        return [
            pull_request for pull_request in pull_requests
            if any(release.id == release_id for release in PullRequestFilterUtils._releases_of(pull_request))
        ]

    @staticmethod
    def _iteration_of(pull_request: PullRequestData) -> Optional[str]:
        linked_task = pull_request.linked_task
        return linked_task.iteration if linked_task and linked_task.iteration else None

    @staticmethod
    def _releases_of(pull_request: PullRequestData) -> List[ReleaseData]:
        linked_task = pull_request.linked_task
        return linked_task.releases if linked_task and linked_task.releases else []
