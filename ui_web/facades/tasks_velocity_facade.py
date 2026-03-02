from datetime import datetime
from typing import Dict, List, Optional, Callable

from tasks.app.domain.model.task import EnrichmentOptions
from ..convertors.velocity_task_detail_convertor import VelocityTaskDetailConvertor
from ..data.velocity_task_detail_data import TaskVelocityData


class TasksVelocityFacade:

    def __init__(self, task_search_api,
                 create_velocity_search_criteria: Callable,
                 resolve_member_group_members: Callable,
                 velocity_task_detail_convertor: VelocityTaskDetailConvertor,
                 in_progress_status_codes: List[str],
                 member_group_custom_filters: Optional[Dict[str, str]] = None):
        self._task_search_api = task_search_api
        self._create_velocity_search_criteria = create_velocity_search_criteria
        self._resolve_member_group_members = resolve_member_group_members
        self._velocity_task_detail_convertor = velocity_task_detail_convertor
        self._in_progress_status_codes = in_progress_status_codes
        self._member_group_custom_filters = member_group_custom_filters

    async def get_tasks(self, developer_names: List[str],
                        start_date: datetime, end_date: datetime,
                        member_group_id: Optional[str] = None,
                        include_all_statuses: bool = False) -> List[TaskVelocityData]:
        tasks = await self._search_tasks(start_date, end_date, member_group_id, include_all_statuses)
        return self._velocity_task_detail_convertor.convert_tasks_to_developers_breakdown(tasks, developer_names)

    async def get_team_tasks(self, start_date: datetime, end_date: datetime,
                             member_group_id: Optional[str] = None,
                             use_custom_filter: bool = False) -> List[TaskVelocityData]:
        custom_query = self._get_custom_filter(member_group_id) if use_custom_filter else None
        tasks = await self._search_tasks(start_date, end_date, member_group_id, False, custom_query)
        all_developer_names = TasksVelocityFacade._extract_developer_names(tasks)
        return self._velocity_task_detail_convertor.convert_tasks_to_developers_breakdown(tasks, all_developer_names)

    @staticmethod
    def _extract_developer_names(tasks):
        names = set()
        for task in tasks:
            if task.time_tracking and task.time_tracking.spent_time_by_assignee:
                names.update(task.time_tracking.spent_time_by_assignee.keys())
        return list(names)

    async def _search_tasks(self, start_date: datetime, end_date: datetime,
                             member_group_id: Optional[str],
                             include_all_statuses: bool,
                             custom_query: Optional[str] = None):
        criteria = self._create_search_criteria(start_date, end_date, member_group_id, include_all_statuses, custom_query)
        enrichment = EnrichmentOptions(
            include_time_tracking=True,
            worklog_transition_statuses=self._in_progress_status_codes
        )
        return await self._task_search_api.search(criteria, enrichment)

    def _create_search_criteria(self, start_date: datetime, end_date: datetime,
                                 member_group_id: Optional[str],
                                 include_all_statuses: bool,
                                 custom_query: Optional[str] = None):
        criteria = self._create_velocity_search_criteria(start_date, end_date)
        if include_all_statuses:
            criteria.status_filter = None
            criteria.resolution_date_range = None
            criteria.last_modified_date_range = (start_date, end_date)
        self._apply_member_group_filter(criteria, member_group_id, custom_query)
        return criteria

    def _apply_member_group_filter(self, criteria, member_group_id: Optional[str],
                                   custom_query: Optional[str] = None):
        if custom_query:
            criteria.raw_jql_filter = custom_query
            return
        members = self._resolve_member_group_members(member_group_id)
        if members:
            criteria.assignee_filter = members

    def _get_custom_filter(self, member_group_id: Optional[str]) -> Optional[str]:
        if not member_group_id or not self._member_group_custom_filters:
            return None
        return self._member_group_custom_filters.get(member_group_id)
