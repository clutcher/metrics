from datetime import date, datetime
from typing import List, Optional

from velocity.app.domain.model.velocity import VelocityReport
from ..data.velocity_report_data import VelocityReportData


class VelocityReportConvertor:
    
    def __init__(self, assignee_search_api):
        self.assignee_search_api = assignee_search_api
    
    def convert_velocity_reports_to_data(self, velocity_reports: List[VelocityReport]) -> List[VelocityReportData]:
        if not velocity_reports:
            return []
        
        return [self._convert_velocity_report_to_data(report) for report in velocity_reports]
    
    def convert_velocity_reports_to_data_with_names(self, velocity_reports: List[VelocityReport]) -> List[VelocityReportData]:
        if not velocity_reports:
            return []
        
        return [self._convert_velocity_report_to_data_with_name(report) for report in velocity_reports]
    
    @staticmethod
    def _convert_velocity_report_to_data(velocity_report: VelocityReport) -> VelocityReportData:
        start_date = velocity_report.start_date
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        elif not isinstance(start_date, date):
            start_date = date.today()
        
        metric_scope_name = None
        if velocity_report.metric_scope_name:
            metric_scope_name = velocity_report.metric_scope_name
        elif velocity_report.metric_scope:
            metric_scope_name = velocity_report.metric_scope or 'Unknown'
        
        return VelocityReportData(
            start_date=start_date,
            velocity=velocity_report.velocity,
            story_points=velocity_report.story_points,
            metric_scope=velocity_report.metric_scope,
            metric_scope_name=metric_scope_name
        )
    
    def _convert_velocity_report_to_data_with_name(self, velocity_report: VelocityReport) -> VelocityReportData:
        data = self._convert_velocity_report_to_data(velocity_report)
        
        if velocity_report.metric_scope:
            data.metric_scope_name = self._resolve_assignee_display_name(velocity_report.metric_scope)
        
        return data
    
    def _resolve_assignee_display_name(self, assignee_id: Optional[str]) -> str:
        if not assignee_id:
            return 'Unknown Assignee'
        
        assignee = self.assignee_search_api.get_assignee_by_id(assignee_id)
        if assignee and assignee.display_name:
            display_name = assignee.display_name.strip()
            if display_name:
                return display_name
        
        if len(assignee_id) > 8 and '-' in assignee_id:
            return f"Assignee {assignee_id[:8]}"
        
        return assignee_id