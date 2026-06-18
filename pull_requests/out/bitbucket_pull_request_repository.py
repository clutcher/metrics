import asyncio
from typing import Any, Dict, List, Optional

from atlassian.bitbucket import Cloud

from .convertors.bitbucket import BitbucketPullRequestConverter
from .convertors.bitbucket_review import BitbucketReviewConverter
from ..app.domain.model.config import PullRequestsConfig
from ..app.domain.model.pull_request import PullRequest, PullRequestRef, PullRequestSearchCriteria
from ..app.domain.model.review import ReviewInputs
from ..app.spi.pull_request_repository import PullRequestRepository

_BITBUCKET_STATE_BY_CRITERIA = {
    'active': 'OPEN',
    'open': 'OPEN',
}


class BitbucketPullRequestRepository(PullRequestRepository):

    def __init__(self, config: PullRequestsConfig):
        bitbucket_config = config.bitbucket
        if not config.is_bitbucket_configured():
            raise ValueError("Missing Bitbucket authentication configuration")

        self._workspace = bitbucket_config.workspace
        self._repositories = bitbucket_config.repositories
        self._converter = BitbucketPullRequestConverter()
        self._review_converter = BitbucketReviewConverter()
        self._cloud = Cloud(
            url=bitbucket_config.url or "https://api.bitbucket.org/",
            username=bitbucket_config.username,
            password=bitbucket_config.app_password,
            cloud=True
        )

    async def find_all(self, criteria: PullRequestSearchCriteria) -> List[PullRequest]:
        state = _BITBUCKET_STATE_BY_CRITERIA.get(criteria.status_filter, 'OPEN')
        pull_requests_by_repository = await asyncio.gather(
            *[self._fetch_repository_pull_requests(repository, state) for repository in self._repositories]
        )
        return [pull_request for repository_pull_requests in pull_requests_by_repository
                for pull_request in repository_pull_requests]

    async def fetch_review_inputs(self, ref: PullRequestRef) -> ReviewInputs:
        repository = ref.repository_id
        detail, activity = await asyncio.gather(
            asyncio.to_thread(self._get_pull_request_detail, repository, ref.pull_request_id),
            asyncio.to_thread(self._list_activity, repository, ref.pull_request_id)
        )
        build_statuses = await asyncio.to_thread(self._list_build_statuses, repository, self._source_commit(detail))
        return self._review_converter.to_review_inputs(detail.get('participants'), activity, build_statuses)

    def _list_activity(self, repository: str, pull_request_id: str) -> List[Dict[str, Any]]:
        path = f"repositories/{self._workspace}/{repository}/pullrequests/{pull_request_id}/activity"
        return self._collect_paged_values(path)

    def _list_build_statuses(self, repository: str, commit_hash: Optional[str]) -> List[Dict[str, Any]]:
        if not commit_hash:
            return []
        path = f"repositories/{self._workspace}/{repository}/commit/{commit_hash}/statuses"
        return [build_status for build_status in self._collect_paged_values(path)
                if build_status.get('type') == 'build']

    @staticmethod
    def _source_commit(detail: Dict[str, Any]) -> Optional[str]:
        source = detail.get('source') or {}
        commit = source.get('commit') or {}
        return commit.get('hash')

    async def _fetch_repository_pull_requests(self, repository: str, state: str) -> List[PullRequest]:
        raw_pull_requests = await asyncio.to_thread(self._query_repository_pull_requests, repository, state)
        return [self._converter.convert_to_pull_request(raw_pull_request, repository)
                for raw_pull_request in raw_pull_requests]

    def _query_repository_pull_requests(self, repository: str, state: str) -> List[Dict[str, Any]]:
        summaries = self._list_pull_requests(repository, state)
        return [self._get_pull_request_detail(repository, summary['id']) for summary in summaries]

    def _list_pull_requests(self, repository: str, state: str) -> List[Dict[str, Any]]:
        path = f"repositories/{self._workspace}/{repository}/pullrequests"
        return self._collect_paged_values(path, params={'state': state, 'pagelen': 50})

    def _collect_paged_values(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        response = self._cloud.get(path, params=params)
        values = []
        while response:
            values.extend(response.get('values', []))
            next_url = response.get('next')
            if not next_url:
                break
            response = self._cloud.get(next_url, absolute=True)
        return values

    def _get_pull_request_detail(self, repository: str, pull_request_id: Any) -> Dict[str, Any]:
        path = f"repositories/{self._workspace}/{repository}/pullrequests/{pull_request_id}"
        return self._cloud.get(path)
