import asyncio
from typing import Any, Dict, List

from atlassian.bitbucket import Cloud

from .convertors.bitbucket import BitbucketPullRequestConverter
from ..app.domain.model.config import PullRequestsConfig
from ..app.domain.model.pull_request import PullRequest, PullRequestSearchCriteria
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

    async def _fetch_repository_pull_requests(self, repository: str, state: str) -> List[PullRequest]:
        raw_pull_requests = await asyncio.to_thread(self._query_repository_pull_requests, repository, state)
        return [self._converter.convert_to_pull_request(raw_pull_request, repository)
                for raw_pull_request in raw_pull_requests]

    def _query_repository_pull_requests(self, repository: str, state: str) -> List[Dict[str, Any]]:
        summaries = self._list_pull_requests(repository, state)
        return [self._get_pull_request_detail(repository, summary['id']) for summary in summaries]

    def _list_pull_requests(self, repository: str, state: str) -> List[Dict[str, Any]]:
        path = f"repositories/{self._workspace}/{repository}/pullrequests"
        response = self._cloud.get(path, params={'state': state, 'pagelen': 50})
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
