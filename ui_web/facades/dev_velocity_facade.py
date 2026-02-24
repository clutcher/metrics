from typing import Optional, List

from sd_metrics_lib.utils.time import TimeUnit

from velocity.app.domain.model.velocity import ReportGenerationParameters, ReportType
from ..convertors.member_convertor import MemberConvertor
from ..convertors.velocity_chart_convertor import VelocityChartConvertor
from ..convertors.velocity_report_convertor import VelocityReportConvertor
from ..data.chart_data import ChartData
from ..data.velocity_report_data import VelocityReportData
from ..utils.chart_transform_utils import ChartTransformUtils


class DevVelocityFacade:
    def __init__(self, velocity_api, assignee_search_api, available_member_groups,
                 create_velocity_search_criteria,
                 member_convertor: MemberConvertor,
                 velocity_chart_convertor: VelocityChartConvertor,
                 velocity_report_convertor: VelocityReportConvertor):
        self.velocity_api = velocity_api
        self.assignee_search_api = assignee_search_api
        self.available_member_groups = available_member_groups
        self.create_velocity_search_criteria = create_velocity_search_criteria
        self.member_convertor = member_convertor
        self.velocity_chart_convertor = velocity_chart_convertor
        self.velocity_report_convertor = velocity_report_convertor

    async def get_velocity_reports_data(self, member_group_id: Optional[str] = None,
                                         number_of_periods: int = 6) -> List[VelocityReportData]:
        velocity_reports = await self._get_velocity_reports(member_group_id, number_of_periods)
        return self.velocity_report_convertor.convert_velocity_reports_to_data_with_names(velocity_reports)

    def get_velocity_chart_data(self, velocity_reports_data: List[VelocityReportData],
                                rolling_avg_window: int = 0,
                                display_periods: int = 0) -> Optional[ChartData]:
        chart = self.velocity_chart_convertor.convert_dev_velocity_reports_to_velocity_chart(velocity_reports_data)
        if rolling_avg_window > 0 and chart:
            chart = ChartTransformUtils.apply_rolling_average(chart, rolling_avg_window)
        if display_periods > 0 and chart:
            chart = ChartTransformUtils.trim_to_last_n_periods(chart, display_periods)
        return chart

    def get_story_points_chart_data(self, velocity_reports_data: List[VelocityReportData],
                                    rolling_avg_window: int = 0,
                                    display_periods: int = 0) -> Optional[ChartData]:
        chart = self.velocity_chart_convertor.convert_dev_velocity_reports_to_story_points_chart(velocity_reports_data)
        if rolling_avg_window > 0 and chart:
            chart = ChartTransformUtils.apply_rolling_average(chart, rolling_avg_window)
        if display_periods > 0 and chart:
            chart = ChartTransformUtils.trim_to_last_n_periods(chart, display_periods)
        return chart

    async def _get_velocity_reports(self, member_group_id: Optional[str],
                                    number_of_periods: int = 6):
        criteria = ReportGenerationParameters(
            time_unit=TimeUnit.MONTH,
            number_of_periods=number_of_periods,
            report_type=ReportType.MEMBER_SCOPE,
            scope_id=member_group_id
        )
        return await self.velocity_api.generate_velocity_report(criteria)
