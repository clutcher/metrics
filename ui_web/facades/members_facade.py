from datetime import timedelta
from typing import List, Optional

from django.conf import settings
from django.utils import timezone

from tasks.app.api.api_for_task_search import ApiForTaskSearch
from tasks.app.domain.model.task import Task, TaskSearchCriteria, EnrichmentOptions, WorkTimeExtractorType
from ..convertors.member_convertor import MemberConvertor
from ..data.member_data import MemberData
from ..data.task_data import TaskData
from ..utils.federated_data_fetcher import FederatedDataFetcher
from ..utils.tasks_utils import TasksUtils


class MembersFacade:

    def __init__(self, task_search_api: ApiForTaskSearch, member_convertor: MemberConvertor) -> None:
        self.task_search_api = task_search_api
        self.member_convertor = member_convertor

    async def get_available_members(self, all_tasks: List[TaskData], member_group_id: Optional[str] = None) -> List[MemberData]:
        current_tasks = TasksUtils.filter_in_progress_tasks(all_tasks)
        available_member_ids = TasksUtils.get_members_not_assigned_to_tasks(current_tasks, member_group_id)
        
        if not available_member_ids:
            return []

        member_workload_data = await self._fetch_member_workload_data(available_member_ids)
        return self.member_convertor.convert_members_with_workload_to_data(available_member_ids, member_workload_data)

    async def _fetch_member_workload_data(self, member_ids: List[str]) -> List[Task]:
        return await (
            self._build_member_fetcher(member_ids)
            .fetch()
        )

    def _build_member_fetcher(self, member_ids: List[str]) -> FederatedDataFetcher:
        return (
            FederatedDataFetcher
            .for_(lambda: self._search_member_workload_tasks(member_ids))
        )

    async def _search_member_workload_tasks(self, member_ids: List[str]) -> List[Task]:
        if not member_ids or not self.task_search_api:
            return []

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        search_criteria = TaskSearchCriteria(
            assignees_history_filter=member_ids,
            last_modified_date_range=(thirty_days_ago, now)
        )

        enrichment = EnrichmentOptions(
            include_time_tracking=True,
            worktime_extractor_type=WorkTimeExtractorType.BOUNDARY_FROM_LAST_MODIFIED,
            worklog_transition_statuses=settings.METRICS_IN_PROGRESS_STATUS_CODES
        )

        return await self.task_search_api.search(search_criteria, enrichment)