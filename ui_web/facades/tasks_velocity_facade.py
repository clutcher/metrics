from datetime import datetime
from typing import List, Optional, Callable

from tasks.app.domain.model.task import EnrichmentOptions
from ..convertors.velocity_task_detail_convertor import VelocityTaskDetailConvertor
from ..data.velocity_task_detail_data import TaskVelocityData


class TasksVelocityFacade:

    def __init__(self, task_search_api,
                 create_velocity_search_criteria: Callable,
                 resolve_member_group_members: Callable,
                 velocity_task_detail_convertor: VelocityTaskDetailConvertor,
                 in_progress_status_codes: List[str]):
        self._task_search_api = task_search_api
        self._create_velocity_search_criteria = create_velocity_search_criteria
        self._resolve_member_group_members = resolve_member_group_members
        self._velocity_task_detail_convertor = velocity_task_detail_convertor
        self._in_progress_status_codes = in_progress_status_codes

    async def get_tasks(self, developer_names: List[str],
                        start_date: datetime, end_date: datetime,
                        member_group_id: Optional[str] = None,
                        include_all_statuses: bool = False) -> List[TaskVelocityData]:
        tasks = await self._search_tasks(start_date, end_date, member_group_id, include_all_statuses)
        return self._velocity_task_detail_convertor.convert_tasks_to_developers_breakdown(tasks, developer_names)

    async def _search_tasks(self, start_date: datetime, end_date: datetime,
                             member_group_id: Optional[str],
                             include_all_statuses: bool):
        criteria = self._create_search_criteria(start_date, end_date, member_group_id, include_all_statuses)
        enrichment = EnrichmentOptions(
            include_time_tracking=True,
            worklog_transition_statuses=self._in_progress_status_codes
        )
        return await self._task_search_api.search(criteria, enrichment)

    def _create_search_criteria(self, start_date: datetime, end_date: datetime,
                                 member_group_id: Optional[str],
                                 include_all_statuses: bool):
        criteria = self._create_velocity_search_criteria(start_date, end_date)
        if include_all_statuses:
            criteria.status_filter = None
            criteria.resolution_date_range = None
            criteria.last_modified_date_range = (start_date, end_date)
        members = self._resolve_member_group_members(member_group_id)
        if members:
            criteria.assignee_filter = members
        return criteria
