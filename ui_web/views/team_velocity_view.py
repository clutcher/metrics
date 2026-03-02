import asyncio

from django.views.generic import TemplateView

from ..container import ui_web_container
from ..utils.chart_json_utils import ChartJsonUtils
from ..utils.velocity_sort_utils import VelocitySortUtils
from .dev_velocity_view import BaseVelocityTasksView


class TeamVelocityView(TemplateView):
    template_name = 'team_velocity.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.team_velocity_facade = ui_web_container.team_velocity_facade

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["partials/team_velocity_content.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        team_id = kwargs.get('team_id')
        member_group_id = team_id or self.request.GET.get('member_group_id')
        rolling_avg = int(self.request.GET.get('rolling_avg', 0))

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 12

        try:
            velocity_reports_data = asyncio.run(
                self.team_velocity_facade.get_velocity_reports_data(member_group_id, 12 + extra_periods)
            )

            velocity_chart = self.team_velocity_facade.get_velocity_chart_data(
                velocity_reports_data, rolling_avg, display_periods if rolling_avg > 0 else 0
            )
            if velocity_chart and velocity_chart.labels:
                VelocitySortUtils.sort_chart_data_chronologically(velocity_chart)

            story_points_chart = self.team_velocity_facade.get_story_points_chart_data(velocity_reports_data)
            if story_points_chart and story_points_chart.labels:
                VelocitySortUtils.sort_chart_data_chronologically(story_points_chart)

            context["month_velocity"] = ChartJsonUtils.convert_chart_data_to_chartjs_json(
                velocity_chart) if velocity_chart else "{}"
            context["month_sp"] = ChartJsonUtils.convert_chart_data_to_chartjs_json(
                story_points_chart) if story_points_chart else "{}"
            context["success"] = True
        except Exception as e:
            context["month_velocity"] = "{}"
            context["month_sp"] = "{}"
            context["success"] = False
            context["error"] = str(e)

        context["build_page_title"] = 'Team Velocity Dashboard'
        context["velocity_rolling_avg"] = rolling_avg
        context["member_group_id"] = member_group_id or ''
        context["has_custom_filter"] = self.team_velocity_facade.has_custom_filter(member_group_id)

        return context


class TeamVelocityTasksView(BaseVelocityTasksView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        period, member_group_id, use_custom_filter = self._parse_request_params()

        try:
            start_date, end_date = self._parse_month_period(period)
            velocity_tasks = asyncio.run(
                self.tasks_velocity_facade.get_team_tasks(
                    start_date, end_date, member_group_id, use_custom_filter
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
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'
        return period, member_group_id, use_custom_filter


class TeamVelocityChartView(TemplateView):
    template_name = 'partials/team_velocity_chart.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.team_velocity_facade = ui_web_container.team_velocity_facade

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        member_group_id = self.request.GET.get('member_group_id')
        rolling_avg = int(self.request.GET.get('rolling_avg', 0))
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 12

        try:
            velocity_reports_data = asyncio.run(
                self.team_velocity_facade.get_velocity_reports_data(
                    member_group_id, 12 + extra_periods, use_custom_filter
                )
            )

            velocity_chart = self.team_velocity_facade.get_velocity_chart_data(
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
        context["use_custom_filter"] = use_custom_filter
        context["has_custom_filter"] = self.team_velocity_facade.has_custom_filter(member_group_id)

        return context


class TeamStoryPointsChartView(TemplateView):
    template_name = 'partials/team_story_points_chart.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.team_velocity_facade = ui_web_container.team_velocity_facade

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        member_group_id = self.request.GET.get('member_group_id')
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        try:
            velocity_reports_data = asyncio.run(
                self.team_velocity_facade.get_velocity_reports_data(
                    member_group_id, 12, use_custom_filter
                )
            )

            story_points_chart = self.team_velocity_facade.get_story_points_chart_data(velocity_reports_data)
            if story_points_chart and story_points_chart.labels:
                VelocitySortUtils.sort_chart_data_chronologically(story_points_chart)

            context["month_sp"] = ChartJsonUtils.convert_chart_data_to_chartjs_json(story_points_chart) if story_points_chart else "{}"
        except Exception as e:
            context["month_sp"] = "{}"
            context["error"] = str(e)

        context["member_group_id"] = member_group_id or ''
        context["use_custom_filter"] = use_custom_filter
        context["has_custom_filter"] = self.team_velocity_facade.has_custom_filter(member_group_id)

        return context
