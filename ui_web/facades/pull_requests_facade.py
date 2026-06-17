from typing import Any, Dict, List, Optional, Tuple

from pull_requests.app.domain.model.pull_request import PullRequest
from tasks.app.domain.model.config import SortingConfig
from tasks.app.domain.model.task import Task
from ..convertors.pull_request_convertor import PullRequestConvertor
from ..data.pull_request_data import PullRequestData
from ..utils.task_sort_utils import TaskSortUtils


class PullRequestsFacade:

    def __init__(self, pull_request_search_api, task_search_api,
                 pull_request_convertor: PullRequestConvertor,
                 sorting_config: SortingConfig,
                 members: Dict[str, Dict[str, Any]],
                 enabled: bool):
        self._pull_request_search_api = pull_request_search_api
        self._task_search_api = task_search_api
        self._pull_request_convertor = pull_request_convertor
        self._sorting_config = sorting_config
        self._members = members or {}
        self._enabled = enabled

    def is_pull_requests_enabled(self) -> bool:
        return self._enabled

    async def get_pull_requests(self, member_group_id: Optional[str] = None) -> List[PullRequestData]:
        if not self._enabled:
            return []

        pull_requests = await self._pull_request_search_api.search()
        pull_requests = self._filter_by_member_group(pull_requests, member_group_id)
        linked_tasks_by_id = await self._fetch_linked_tasks(pull_requests)
        sorted_pull_requests = self._sort_by_ticket_priority(pull_requests, linked_tasks_by_id)

        return [
            self._pull_request_convertor.convert_to_data(pull_request, linked_tasks_by_id.get(pull_request.linked_task_id))
            for pull_request in sorted_pull_requests
        ]

    def _filter_by_member_group(self, pull_requests: List[PullRequest],
                                member_group_id: Optional[str]) -> List[PullRequest]:
        if not member_group_id:
            return pull_requests
        return [pull_request for pull_request in pull_requests
                if member_group_id in self._author_member_groups(pull_request)]

    def _author_member_groups(self, pull_request: PullRequest) -> List[str]:
        author_data = self._members.get(pull_request.author.display_name, {})
        return author_data.get('member_groups', [])

    async def _fetch_linked_tasks(self, pull_requests: List[PullRequest]) -> Dict[str, Task]:
        task_ids = sorted({pull_request.linked_task_id for pull_request in pull_requests if pull_request.linked_task_id})
        if not task_ids:
            return {}
        tasks = await self._task_search_api.search_by_ids(task_ids)
        return {task.id: task for task in tasks}

    def _sort_by_ticket_priority(self, pull_requests: List[PullRequest],
                                 linked_tasks_by_id: Dict[str, Task]) -> List[PullRequest]:
        with_ticket: List[Tuple[PullRequest, Task]] = []
        without_ticket: List[PullRequest] = []
        for pull_request in pull_requests:
            linked_task = linked_tasks_by_id.get(pull_request.linked_task_id) if pull_request.linked_task_id else None
            if linked_task:
                with_ticket.append((pull_request, linked_task))
            else:
                without_ticket.append(pull_request)

        with_ticket.sort(key=self._linked_ticket_sort_key)

        return [pull_request for pull_request, _ in with_ticket] + without_ticket

    def _linked_ticket_sort_key(self, pull_request_with_task: Tuple[PullRequest, Task]) -> Tuple[Any, ...]:
        _, linked_task = pull_request_with_task
        return TaskSortUtils.build_sort_key(linked_task, self._sorting_config)
