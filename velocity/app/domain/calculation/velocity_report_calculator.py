from copy import deepcopy
from datetime import datetime
from typing import Optional, List, Callable

from sd_metrics_lib.calculators.velocity import GeneralizedTeamVelocityCalculator, UserVelocityCalculator
from sd_metrics_lib.sources.tasks import ProxyTaskProvider

from velocity.app.domain.calculation.member_group_resolver import MemberGroupResolver
from velocity.app.domain.calculation.proxy_extractors import (
    TaskModuleStoryPointExtractor, TaskModuleTotalSpentTimeExtractor, TaskModuleWorklogExtractor
)
from velocity.app.domain.model.config import VelocityConfig
from velocity.app.domain.model.velocity import VelocityReport
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
                                                   scope_id: Optional[str] = None) -> VelocityReport:
        tasks = await self._fetch_tasks_for_period(start_date, end_date, scope_id)

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
                                                           scope_id: Optional[str] = None) -> List[VelocityReport]:
        tasks = await self._fetch_tasks_for_period(start_date, end_date, scope_id)

        if not tasks:
            return []

        velocity_calculator = UserVelocityCalculator(
            task_provider=ProxyTaskProvider(tasks),
            story_point_extractor=TaskModuleStoryPointExtractor,
            worklog_extractor=TaskModuleWorklogExtractor
        )
        
        scope_velocities = velocity_calculator.calculate()
        scope_story_points = velocity_calculator.get_story_points()

        velocity_reports = []

        allowed_scope_ids = await self._get_allowed_scope_ids(scope_id)

        for scope_id, velocity in scope_velocities.items():
            if allowed_scope_ids and scope_id not in allowed_scope_ids:
                continue
                
            story_points = scope_story_points.get(scope_id, 0.0)
            
            velocity_reports.append(VelocityReport(
                start_date=start_date,
                end_date=end_date,
                velocity=velocity,
                story_points=story_points,
                metric_scope=scope_id
            ))

        return velocity_reports

    async def _get_allowed_scope_ids(self, member_group_id):
        allowed_scope_ids = None
        if member_group_id:
            allowed_scope_ids = set(self._member_group_resolver.resolve_members(member_group_id) or [])
        return allowed_scope_ids

    def _create_velocity_search_criteria(self, start_date: datetime, end_date: datetime, member_group_id: Optional[str] = None):
        search_criteria = deepcopy(self.__velocity_search_criteria_template)
        search_criteria.resolution_date_range = (start_date, end_date)

        members_of_member_group = self._member_group_resolver.resolve_members(member_group_id)
        if members_of_member_group:
            search_criteria.assignee_filter = members_of_member_group

        return search_criteria

    async def _fetch_tasks_for_period(self, start_date: datetime, end_date: datetime,
                                      member_group_id: Optional[str] = None):
        search_criteria = self._create_velocity_search_criteria(start_date, end_date, member_group_id)
        return await self._task_repository.search(search_criteria)
