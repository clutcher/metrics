from copy import deepcopy
from datetime import datetime
from typing import Optional, List, Callable

from sd_metrics_lib.calculators.velocity import GeneralizedTeamVelocityCalculator, UserVelocityCalculator
from sd_metrics_lib.sources.tasks import ProxyTaskProvider

from tasks.app.domain.model.task import EnrichmentOptions
from velocity.app.domain.calculation.member_group_resolver import MemberGroupResolver
from velocity.app.domain.calculation.proxy_extractors import (
    TaskModuleStoryPointExtractor, TaskModuleTotalSpentTimeExtractor, TaskModuleWorklogExtractor
)
from velocity.app.domain.model.config import VelocityConfig
from velocity.app.domain.model.velocity import TaskFilter, VelocityReport
from velocity.app.spi.task_repository import TaskRepository


class VelocityReportCalculator:

    def __init__(self, task_repository: TaskRepository, configuration: VelocityConfig,
                 member_group_resolver: MemberGroupResolver,
                 velocity_search_criteria_factory: Callable[[], any]):
        self._task_repository = task_repository
        self._configuration = configuration
        self._member_group_resolver = member_group_resolver
        self.__velocity_search_criteria_template = velocity_search_criteria_factory()

    async def calculate_velocity_report_for_period(self,
                                                   start_date: datetime,
                                                   end_date: datetime,
                                                   scope_id: Optional[str] = None,
                                                   task_filter: TaskFilter = None) -> VelocityReport:
        tasks = await self._fetch_tasks_for_period(start_date, end_date, scope_id, task_filter)

        if not tasks:
            return VelocityReport(
                start_date=start_date,
                end_date=end_date,
                velocity=0,
                story_points=0
            )

        velocity_calculator = GeneralizedTeamVelocityCalculator(
            task_provider=ProxyTaskProvider(tasks),
            story_point_extractor=TaskModuleStoryPointExtractor,
            time_extractor=TaskModuleTotalSpentTimeExtractor
        )
        velocity_calculator.calculate()

        velocity = velocity_calculator.get_metric()
        story_points = velocity_calculator.get_story_points()

        return VelocityReport(
            start_date=start_date,
            end_date=end_date,
            velocity=velocity,
            story_points=story_points
        )

    async def calculate_scoped_velocity_reports_for_period(self,
                                                           start_date: datetime,
                                                           end_date: datetime,
                                                           scope_id: Optional[str] = None,
                                                           task_filter: TaskFilter = None) -> List[VelocityReport]:
        tasks = await self._fetch_tasks_for_period(start_date, end_date, scope_id, task_filter)
        allowed_scope_ids = await self._get_allowed_scope_ids(scope_id)

        if not tasks:
            return self._build_zero_velocity_reports(start_date, end_date, allowed_scope_ids)

        velocity_calculator = UserVelocityCalculator(
            task_provider=ProxyTaskProvider(tasks),
            story_point_extractor=TaskModuleStoryPointExtractor,
            worklog_extractor=TaskModuleWorklogExtractor
        )

        scope_velocities = velocity_calculator.calculate()
        scope_story_points = velocity_calculator.get_story_points()

        velocity_reports = []

        for member_id, velocity in scope_velocities.items():
            if allowed_scope_ids and member_id not in allowed_scope_ids:
                continue

            story_points = scope_story_points.get(member_id, 0.0)

            velocity_reports.append(VelocityReport(
                start_date=start_date,
                end_date=end_date,
                velocity=velocity,
                story_points=story_points,
                metric_scope=member_id
            ))

        return velocity_reports

    @staticmethod
    def _build_zero_velocity_reports(start_date: datetime, end_date: datetime,
                                     allowed_scope_ids: Optional[set]) -> List[VelocityReport]:
        if not allowed_scope_ids:
            return []
        return [
            VelocityReport(start_date=start_date, end_date=end_date, velocity=0, story_points=0, metric_scope=member_id)
            for member_id in allowed_scope_ids
        ]

    async def _get_allowed_scope_ids(self, member_group_id):
        allowed_scope_ids = None
        if member_group_id:
            allowed_scope_ids = set(self._member_group_resolver.resolve_members(member_group_id) or [])
        return allowed_scope_ids

    def _create_velocity_search_criteria(self, start_date: datetime, end_date: datetime,
                                          member_group_id: Optional[str] = None,
                                          task_filter: TaskFilter = None):
        search_criteria = deepcopy(self.__velocity_search_criteria_template)

        if self._should_search_all_statuses(task_filter):
            search_criteria.status_filter = None
            search_criteria.resolution_date_range = None
            search_criteria.state_change_date_range = (start_date, end_date)
        else:
            search_criteria.resolution_date_range = (start_date, end_date)

        if self._should_use_customer_member_group_query(task_filter):
            search_criteria.raw_jql_filter = self._should_use_customer_member_group_query(task_filter)
        else:
            members_of_member_group = self._member_group_resolver.resolve_members(member_group_id)
            if members_of_member_group:
                search_criteria.assignee_filter = members_of_member_group

        return search_criteria

    @staticmethod
    def _should_use_customer_member_group_query(task_filter: TaskFilter) -> str | None:
        return task_filter and task_filter.custom_query

    @staticmethod
    def _should_search_all_statuses(task_filter: TaskFilter) -> bool:
        return task_filter and task_filter.include_all_statuses

    async def _fetch_tasks_for_period(self, start_date: datetime, end_date: datetime,
                                      member_group_id: Optional[str] = None,
                                      task_filter: TaskFilter = None):
        search_criteria = self._create_velocity_search_criteria(
            start_date, end_date, member_group_id, task_filter
        )
        enrichment = VelocityReportCalculator._build_enrichment(task_filter)
        return await self._task_repository.search(search_criteria, enrichment)

    @staticmethod
    def _build_enrichment(task_filter: TaskFilter) -> Optional[EnrichmentOptions]:
        if not task_filter or not task_filter.worklog_transition_statuses:
            return None
        return EnrichmentOptions(
            include_time_tracking=True,
            worklog_transition_statuses=task_filter.worklog_transition_statuses
        )
