import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import List, Optional

from sd_metrics_lib.utils.generators import TimeRangeGenerator
from sd_metrics_lib.utils.time import TimeUnit

from velocity.app.domain.calculation.velocity_report_calculator import VelocityReportCalculator
from .model.velocity import ReportGenerationParameters, VelocityReport, ReportType
from ..api.api_for_report_generation import ApiForVelocityReportGeneration

metrics_executor = ThreadPoolExecutor(thread_name_prefix="metrics-calculator")


class ReportGenerationService(ApiForVelocityReportGeneration):

    def __init__(self, calculation_service: VelocityReportCalculator):
        self._calculation_service = calculation_service

    async def generate_velocity_report(self, generation_parameters: ReportGenerationParameters) -> Optional[List[VelocityReport]]:
        if generation_parameters.report_type is None:
            return None
            
        metrics_calculation_function = self._resolve_metrics_calculation_function(generation_parameters.report_type)
        if metrics_calculation_function is None:
            return None
            
        calculation_function = partial(
            metrics_calculation_function,
            scope_id=generation_parameters.scope_id,
            include_all_statuses=generation_parameters.include_all_statuses
        )
        
        period_reports = await self._calculate_time_ranged_data_async(
            generation_parameters.time_unit,
            generation_parameters.number_of_periods,
            calculation_function
        )

        return self._flatten_reports(period_reports)

    def _resolve_metrics_calculation_function(self, report_type: ReportType):
        if report_type is None:
            return None

        if report_type == ReportType.MEMBER_GROUP_SCOPE:
            return self._calculation_service.calculate_velocity_report_for_period
        elif report_type == ReportType.MEMBER_SCOPE:
            return self._calculation_service.calculate_scoped_velocity_reports_for_period
        return None

    @staticmethod
    async def _calculate_time_ranged_data_async(time_unit: TimeUnit, number_of_last_data: int,
                                                metric_calculation_function):
        time_range_generator = TimeRangeGenerator(time_unit, number_of_last_data, datetime.timedelta(1))

        tasks = []
        for start_date, end_date in time_range_generator:
            task = metric_calculation_function(start_date, end_date)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

    @staticmethod
    def _flatten_reports(period_reports) -> List[VelocityReport]:
        all_reports = []
        for reports in period_reports:
            if isinstance(reports, list):
                all_reports.extend(reports)
            else:
                all_reports.append(reports)
        return all_reports
