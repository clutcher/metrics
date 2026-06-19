import asyncio
from typing import List

from azure.devops.connection import Connection
from azure.devops.v7_1.git.models import GitPullRequestSearchCriteria
from msrest.authentication import BasicAuthentication

from .convertors.azure import AzurePullRequestConverter
from .convertors.azure_review import AzureReviewConverter
from ..app.domain.model.config import PullRequestsConfig
from ..app.domain.model.pull_request import PullRequest, PullRequestRef, PullRequestSearchCriteria
from ..app.domain.model.review import ReviewInputs
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
        self._review_converter = AzureReviewConverter()

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

    async def fetch_review_inputs(self, ref: PullRequestRef) -> ReviewInputs:
        reviewers, threads, policy_evaluations, pull_request_detail = await asyncio.gather(
            asyncio.to_thread(self._query_reviewers, ref),
            asyncio.to_thread(self._query_threads, ref),
            asyncio.to_thread(self._query_policy_evaluations, ref),
            asyncio.to_thread(self._query_pull_request_detail, ref)
        )
        azure_merge_status = getattr(pull_request_detail, 'merge_status', None)
        return self._review_converter.to_review_inputs(reviewers, threads, policy_evaluations, azure_merge_status)

    def _query_reviewers(self, ref: PullRequestRef):
        git_client = self._connection.clients.get_git_client()
        return git_client.get_pull_request_reviewers(
            repository_id=ref.repository_id, pull_request_id=int(ref.pull_request_id), project=ref.project_name
        )

    def _query_pull_request_detail(self, ref: PullRequestRef):
        git_client = self._connection.clients.get_git_client()
        return git_client.get_pull_request_by_id(
            pull_request_id=int(ref.pull_request_id), project=ref.project_name
        )

    def _query_threads(self, ref: PullRequestRef):
        git_client = self._connection.clients.get_git_client()
        return git_client.get_threads(
            repository_id=ref.repository_id, pull_request_id=int(ref.pull_request_id), project=ref.project_name
        )

    def _query_policy_evaluations(self, ref: PullRequestRef):
        policy_client = self._connection.clients.get_policy_client()
        artifact_id = f"vstfs:///CodeReview/CodeReviewId/{ref.project_id}/{ref.pull_request_id}"
        return policy_client.get_policy_evaluations(project=ref.project_name, artifact_id=artifact_id)

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
