import asyncio
from typing import List

from azure.devops.connection import Connection
from azure.devops.v7_1.git.models import GitPullRequestSearchCriteria
from msrest.authentication import BasicAuthentication

from .convertors.azure import AzurePullRequestConverter
from ..app.domain.model.config import PullRequestsConfig
from ..app.domain.model.pull_request import PullRequest, PullRequestSearchCriteria
from ..app.spi.pull_request_repository import PullRequestRepository


class AzurePullRequestRepository(PullRequestRepository):

    def __init__(self, config: PullRequestsConfig):
        azure_config = config.azure
        if not config.is_azure_configured():
            raise ValueError("Missing Azure authentication configuration")

        credentials = BasicAuthentication('', azure_config.pat)
        self._connection = Connection(base_url=azure_config.organization_url, creds=credentials)
        self._project_keys = azure_config.project_keys
        self._converter = AzurePullRequestConverter(azure_config)

    async def find_all(self, criteria: PullRequestSearchCriteria) -> List[PullRequest]:
        pull_requests_by_project = await asyncio.gather(
            *[self._fetch_project_pull_requests(project_key, criteria) for project_key in self._project_keys]
        )
        return [pull_request for project_pull_requests in pull_requests_by_project
                for pull_request in project_pull_requests]

    async def _fetch_project_pull_requests(self, project_key: str,
                                           criteria: PullRequestSearchCriteria) -> List[PullRequest]:
        azure_pull_requests = await asyncio.to_thread(self._query_project_pull_requests, project_key, criteria)
        return [self._converter.convert_to_pull_request(azure_pull_request)
                for azure_pull_request in azure_pull_requests]

    _PAGE_SIZE = 1000

    def _query_project_pull_requests(self, project_key: str, criteria: PullRequestSearchCriteria):
        git_client = self._connection.clients.get_git_client()
        search_criteria = GitPullRequestSearchCriteria(status=criteria.status_filter)

        pull_requests_by_id = {}
        skip = 0
        while True:
            page = git_client.get_pull_requests_by_project(
                project=project_key, search_criteria=search_criteria, top=self._PAGE_SIZE, skip=skip
            )
            if not page:
                break
            new_pull_requests = [pr for pr in page if pr.pull_request_id not in pull_requests_by_id]
            if not new_pull_requests:
                break
            for pull_request in new_pull_requests:
                pull_requests_by_id[pull_request.pull_request_id] = pull_request
            skip += self._PAGE_SIZE
        return list(pull_requests_by_id.values())
