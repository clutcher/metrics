import asyncio
import json
from dataclasses import asdict

from django.views.generic import TemplateView

from ..container import ui_web_container
from ..utils.chart_json_utils import ChartJsonUtils
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

        velocity_thresholds = self.dev_velocity_facade.get_velocity_thresholds()
        context["velocity_thresholds"] = json.dumps(asdict(velocity_thresholds))

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 6

        try:
            velocity_reports_data = asyncio.run(
                self.dev_velocity_facade.get_velocity_reports_data(
                    member_group_id, 6 + extra_periods, include_all_statuses
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

        velocity_thresholds = self.dev_velocity_facade.get_velocity_thresholds()
        context["velocity_thresholds"] = json.dumps(asdict(velocity_thresholds))

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 6

        try:
            velocity_reports_data = asyncio.run(
                self.dev_velocity_facade.get_velocity_reports_data(member_group_id, 6 + extra_periods, include_all_statuses)
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

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 6

        try:
            velocity_reports_data = asyncio.run(
                self.dev_velocity_facade.get_velocity_reports_data(member_group_id, 6 + extra_periods, include_all_statuses)
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

        return context
