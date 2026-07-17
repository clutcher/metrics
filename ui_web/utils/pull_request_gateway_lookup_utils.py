from typing import Dict, List, Optional

from pull_requests.app.domain.model.pull_request import PullRequest
from ..data.task_data import LinkedPullRequestData, TaskData


class PullRequestGatewayLookupUtils:

    @staticmethod
    async def populate_linked_pull_requests(tasks_data: List[TaskData], pull_request_search_api) -> None:
        if not pull_request_search_api or not tasks_data:
            return

        pull_requests = await pull_request_search_api.search()
        linked_pull_request_by_task_id = PullRequestGatewayLookupUtils._index_latest_by_task_id(pull_requests)

        for task_data in tasks_data:
            task_data.linked_pull_request = linked_pull_request_by_task_id.get(task_data.id)

    @staticmethod
    def _index_latest_by_task_id(pull_requests: List[PullRequest]) -> Dict[str, LinkedPullRequestData]:
        latest_pull_request_by_task_id: Dict[str, PullRequest] = {}

        for pull_request in pull_requests:
            if not pull_request.linked_task_id:
                continue

            current = latest_pull_request_by_task_id.get(pull_request.linked_task_id)
            if current is None or PullRequestGatewayLookupUtils._is_more_recent(pull_request, current):
                latest_pull_request_by_task_id[pull_request.linked_task_id] = pull_request

        return {
            task_id: PullRequestGatewayLookupUtils._to_linked_pull_request_data(pull_request)
            for task_id, pull_request in latest_pull_request_by_task_id.items()
        }

    @staticmethod
    def _is_more_recent(candidate: PullRequest, current: PullRequest) -> bool:
        if not candidate.created_date or not current.created_date:
            return False
        return candidate.created_date > current.created_date

    @staticmethod
    def _to_linked_pull_request_data(pull_request: PullRequest) -> LinkedPullRequestData:
        return LinkedPullRequestData(
            id=pull_request.id,
            repository_id=pull_request.repository_id,
            project_id=pull_request.project_id,
            project_name=pull_request.project_name,
            url=pull_request.url
        )
