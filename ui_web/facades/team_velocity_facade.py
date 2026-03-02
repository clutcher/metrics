from typing import Dict, Optional, List

from sd_metrics_lib.utils.time import TimeUnit

from velocity.app.domain.model.velocity import ReportGenerationParameters, ReportType, TaskFilter
from ..convertors.member_convertor import MemberConvertor
from ..convertors.velocity_chart_convertor import VelocityChartConvertor
from ..convertors.velocity_report_convertor import VelocityReportConvertor
from ..data.chart_data import ChartData
from ..data.member_data import MemberGroupFilterData
from ..data.velocity_report_data import VelocityReportData
from ..utils.chart_transform_utils import ChartTransformUtils


class TeamVelocityFacade:

    def __init__(self, velocity_api, assignee_search_api, available_member_groups,
                 member_convertor: MemberConvertor,
                 velocity_chart_convertor: VelocityChartConvertor,
                 velocity_report_convertor: VelocityReportConvertor,
                 member_group_custom_filters: Optional[Dict[str, str]] = None):
        self.velocity_api = velocity_api
        self.available_member_groups = available_member_groups
        self.member_convertor = member_convertor
        self.velocity_chart_convertor = velocity_chart_convertor
        self.velocity_report_convertor = velocity_report_convertor
        self._member_group_custom_filters = member_group_custom_filters

    def has_custom_filter(self, member_group_id: Optional[str]) -> bool:
        if not member_group_id or not self._member_group_custom_filters:
            return False
        return member_group_id in self._member_group_custom_filters

    async def get_velocity_reports_data(self, member_group_id: Optional[str] = None,
                                         number_of_periods: int = 12,
                                         use_custom_filter: bool = False) -> List[VelocityReportData]:
        custom_query = self._resolve_custom_query(member_group_id) if use_custom_filter else None
        velocity_reports = await self._get_velocity_reports(member_group_id, number_of_periods, custom_query)
        return self.velocity_report_convertor.convert_velocity_reports_to_data(velocity_reports)

    def get_velocity_chart_data(self, velocity_reports_data: List[VelocityReportData],
                                rolling_avg_window: int = 0,
                                display_periods: int = 0) -> Optional[ChartData]:
        chart = self.velocity_chart_convertor.convert_velocity_reports_to_velocity_chart(velocity_reports_data)
        if rolling_avg_window > 0 and chart:
            chart = ChartTransformUtils.apply_rolling_average(chart, rolling_avg_window)
        if display_periods > 0 and chart:
            chart = ChartTransformUtils.trim_to_last_n_periods(chart, display_periods)
        return chart

    def get_story_points_chart_data(self, velocity_reports_data: List[VelocityReportData]) -> Optional[ChartData]:
        return self.velocity_chart_convertor.convert_velocity_reports_to_story_points_chart(velocity_reports_data)

    def get_filter_state_data(self, member_group_id: Optional[str] = None) -> MemberGroupFilterData:
        member_groups_data = [self.member_convertor.convert_member_group_to_data(group) for group in
                              self.available_member_groups]
        return MemberGroupFilterData(
            selected_member_group_id=member_group_id,
            available_member_groups=member_groups_data
        )

    def _resolve_custom_query(self, member_group_id: Optional[str]) -> Optional[str]:
        if not member_group_id or not self._member_group_custom_filters:
            return None
        return self._member_group_custom_filters.get(member_group_id)

    async def _get_velocity_reports(self, member_group_id: Optional[str],
                                    number_of_periods: int = 12,
                                    custom_query: Optional[str] = None):
        criteria = ReportGenerationParameters(
            time_unit=TimeUnit.MONTH,
            number_of_periods=number_of_periods,
            report_type=ReportType.MEMBER_GROUP_SCOPE,
            scope_id=member_group_id,
            task_filter=TaskFilter(custom_query=custom_query)
        )
        return await self.velocity_api.generate_velocity_report(criteria)
