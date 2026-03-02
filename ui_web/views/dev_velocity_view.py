import asyncio
import calendar
import json
from dataclasses import asdict
from datetime import datetime

from django.views.generic import TemplateView

from ..container import ui_web_container
from ..data.hierarchical_item_data import HierarchicalItemData
from ..utils.chart_json_utils import ChartJsonUtils
from ..utils.task_grouping_utils import TaskGroupingUtils
from ..utils.velocity_sort_utils import VelocitySortUtils


class DevVelocityView(TemplateView):
    template_name = 'dev_velocity.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dev_velocity_facade = ui_web_container.dev_velocity_facade

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["partials/dev_velocity_content.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        team_id = kwargs.get('team_id')
        member_group_id = team_id or self.request.GET.get('member_group_id')
        rolling_avg = int(self.request.GET.get('rolling_avg', 0))
        include_all_statuses = self.request.GET.get('all_tasks') == 'true'
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        velocity_thresholds = self.dev_velocity_facade.get_velocity_thresholds()
        context["velocity_thresholds"] = json.dumps(asdict(velocity_thresholds))

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 6

        try:
            velocity_reports_data = asyncio.run(
                self.dev_velocity_facade.get_velocity_reports_data(
                    member_group_id, 6 + extra_periods, include_all_statuses, use_custom_filter
                )
            )

            velocity_chart = self.dev_velocity_facade.get_velocity_chart_data(
                velocity_reports_data, rolling_avg, display_periods if rolling_avg > 0 else 0
            )
            if velocity_chart and velocity_chart.labels:
                VelocitySortUtils.sort_chart_data_chronologically(velocity_chart)

            story_points_chart = self.dev_velocity_facade.get_story_points_chart_data(
                velocity_reports_data, rolling_avg, display_periods if rolling_avg > 0 else 0
            )
            if story_points_chart and story_points_chart.labels:
                VelocitySortUtils.sort_chart_data_chronologically(story_points_chart)

            context["month_velocity"] = ChartJsonUtils.convert_chart_data_to_chartjs_json(velocity_chart) if velocity_chart else "{}"
            context["month_sp"] = ChartJsonUtils.convert_chart_data_to_chartjs_json(story_points_chart) if story_points_chart else "{}"
            context["success"] = True
        except Exception as e:
            context["month_velocity"] = "{}"
            context["month_sp"] = "{}"
            context["success"] = False
            context["error"] = str(e)

        context["build_page_title"] = 'Developer Velocity Dashboard'
        context["velocity_rolling_avg"] = rolling_avg
        context["sp_rolling_avg"] = rolling_avg
        context["member_group_id"] = member_group_id or ''
        context["include_all_statuses"] = include_all_statuses
        context["use_custom_filter"] = use_custom_filter
        context["has_custom_filter"] = self.dev_velocity_facade.has_custom_filter(member_group_id)

        return context


class DevVelocityChartView(TemplateView):
    template_name = 'partials/dev_velocity_chart.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dev_velocity_facade = ui_web_container.dev_velocity_facade

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        member_group_id = self.request.GET.get('member_group_id')
        rolling_avg = int(self.request.GET.get('rolling_avg', 0))
        include_all_statuses = self.request.GET.get('all_tasks') == 'true'
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        velocity_thresholds = self.dev_velocity_facade.get_velocity_thresholds()
        context["velocity_thresholds"] = json.dumps(asdict(velocity_thresholds))

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 6

        try:
            velocity_reports_data = asyncio.run(
                self.dev_velocity_facade.get_velocity_reports_data(member_group_id, 6 + extra_periods, include_all_statuses, use_custom_filter)
            )

            velocity_chart = self.dev_velocity_facade.get_velocity_chart_data(
                velocity_reports_data, rolling_avg, display_periods if rolling_avg > 0 else 0
            )
            if velocity_chart and velocity_chart.labels:
                VelocitySortUtils.sort_chart_data_chronologically(velocity_chart)

            context["month_velocity"] = ChartJsonUtils.convert_chart_data_to_chartjs_json(velocity_chart) if velocity_chart else "{}"
        except Exception as e:
            context["month_velocity"] = "{}"
            context["error"] = str(e)

        context["velocity_rolling_avg"] = rolling_avg
        context["member_group_id"] = member_group_id or ''
        context["include_all_statuses"] = include_all_statuses
        context["use_custom_filter"] = use_custom_filter
        context["has_custom_filter"] = self.dev_velocity_facade.has_custom_filter(member_group_id)

        return context


class DevStoryPointsChartView(TemplateView):
    template_name = 'partials/dev_story_points_chart.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dev_velocity_facade = ui_web_container.dev_velocity_facade

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        member_group_id = self.request.GET.get('member_group_id')
        rolling_avg = int(self.request.GET.get('rolling_avg', 0))
        include_all_statuses = self.request.GET.get('all_tasks') == 'true'
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 6

        try:
            velocity_reports_data = asyncio.run(
                self.dev_velocity_facade.get_velocity_reports_data(member_group_id, 6 + extra_periods, include_all_statuses, use_custom_filter)
            )

            story_points_chart = self.dev_velocity_facade.get_story_points_chart_data(
                velocity_reports_data, rolling_avg, display_periods if rolling_avg > 0 else 0
            )
            if story_points_chart and story_points_chart.labels:
                VelocitySortUtils.sort_chart_data_chronologically(story_points_chart)

            context["month_sp"] = ChartJsonUtils.convert_chart_data_to_chartjs_json(story_points_chart) if story_points_chart else "{}"
        except Exception as e:
            context["month_sp"] = "{}"
            context["error"] = str(e)

        context["sp_rolling_avg"] = rolling_avg
        context["member_group_id"] = member_group_id or ''
        context["include_all_statuses"] = include_all_statuses
        context["use_custom_filter"] = use_custom_filter
        context["has_custom_filter"] = self.dev_velocity_facade.has_custom_filter(member_group_id)

        return context


class BaseVelocityTasksView(TemplateView):
    template_name = 'partials/dev_velocity_tasks.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tasks_velocity_facade = ui_web_container.tasks_velocity_facade
        self.summary_convertor = ui_web_container.developer_velocity_summary_convertor

    def _build_task_hierarchy(self, velocity_tasks, period):
        developer_groups = self._group_by_developer(velocity_tasks)
        total_count = sum(g.count for g in developer_groups)
        return [HierarchicalItemData(
            name=f"Tasks — {period}",
            type="member_group",
            count=total_count,
            items=developer_groups
        )]

    def _group_by_developer(self, velocity_tasks):
        groups = TaskGroupingUtils.group_tasks_by_key(
            velocity_tasks,
            key_extractor=lambda t: t.assignment.assignee.display_name,
            group_type="task_velocity"
        )
        return self.summary_convertor.enrich_with_summaries(groups)

    @staticmethod
    def _parse_month_period(period: str):
        year, month = int(period[:4]), int(period[5:7])
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, 1), datetime(year, month, last_day)


class DevVelocityTasksView(BaseVelocityTasksView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        developer_names, period, member_group_id, include_all_statuses, use_custom_filter = self._parse_request_params()

        try:
            start_date, end_date = self._parse_month_period(period)
            velocity_tasks = asyncio.run(
                self.tasks_velocity_facade.get_tasks(
                    developer_names, start_date, end_date, member_group_id, include_all_statuses, use_custom_filter
                )
            )
            context["task_groups"] = self._build_task_hierarchy(velocity_tasks, period)
        except Exception as e:
            context["task_groups"] = []
            context["error"] = str(e)

        return context

    def _parse_request_params(self):
        period = self.request.GET.get('period', '')
        member_group_id = self.request.GET.get('member_group_id')
        include_all_statuses = self.request.GET.get('all_tasks') == 'true'
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        developers_param = self.request.GET.get('developers', '')
        developer_names = [d.strip() for d in developers_param.split(',') if d.strip()]

        return developer_names, period, member_group_id, include_all_statuses, use_custom_filter
