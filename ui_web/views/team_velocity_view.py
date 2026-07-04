import asyncio

from ..container import ui_web_container
from ..utils.chart_json_utils import ChartJsonUtils
from ..utils.velocity_sort_utils import VelocitySortUtils
from .dev_velocity_view import BaseVelocityTasksView
from .graceful_template_view import GracefulTemplateView


class TeamVelocityView(GracefulTemplateView):
    template_name = 'team_velocity.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.team_velocity_facade = ui_web_container.team_velocity_facade

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["partials/team_velocity_content.html"]
        return [self.template_name]

    def populate_context(self, context, **kwargs):
        team_id = kwargs.get('team_id')
        member_group_id = team_id or self.request.GET.get('member_group_id')
        rolling_avg = int(self.request.GET.get('rolling_avg', 0))
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        context["month_velocity"] = "{}"
        context["month_sp"] = "{}"
        context["success"] = False
        context["build_page_title"] = 'Team Velocity Dashboard'
        context["velocity_rolling_avg"] = rolling_avg
        context["member_group_id"] = member_group_id or ''
        context["use_custom_filter"] = use_custom_filter
        context["has_custom_filter"] = self.team_velocity_facade.has_custom_filter(member_group_id)
        context["selected_period"] = self.request.GET.get('period', '')

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 12

        velocity_reports_data = asyncio.run(
            self.team_velocity_facade.get_velocity_reports_data(member_group_id, 12 + extra_periods, use_custom_filter)
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


class TeamVelocityTasksView(BaseVelocityTasksView):

    def populate_context(self, context, **kwargs):
        context["task_groups"] = []

        period, member_group_id, use_custom_filter = self._parse_request_params()

        start_date, end_date = self._parse_month_period(period)
        velocity_tasks = asyncio.run(
            self.tasks_velocity_facade.get_team_tasks(
                start_date, end_date, member_group_id, use_custom_filter
            )
        )
        context["task_groups"] = self._build_task_hierarchy(velocity_tasks, period)

    def _parse_request_params(self):
        period = self.request.GET.get('period', '')
        member_group_id = self.request.GET.get('member_group_id')
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'
        return period, member_group_id, use_custom_filter


class TeamVelocityChartView(GracefulTemplateView):
    template_name = 'partials/team_velocity_chart.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.team_velocity_facade = ui_web_container.team_velocity_facade

    def populate_context(self, context, **kwargs):
        member_group_id = self.request.GET.get('member_group_id')
        rolling_avg = int(self.request.GET.get('rolling_avg', 0))
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        context["month_velocity"] = "{}"
        context["velocity_rolling_avg"] = rolling_avg
        context["member_group_id"] = member_group_id or ''
        context["use_custom_filter"] = use_custom_filter
        context["has_custom_filter"] = self.team_velocity_facade.has_custom_filter(member_group_id)
        context["selected_period"] = self.request.GET.get('period', '')

        extra_periods = rolling_avg - 1 if rolling_avg > 0 else 0
        display_periods = 12

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


class TeamStoryPointsChartView(GracefulTemplateView):
    template_name = 'partials/team_story_points_chart.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.team_velocity_facade = ui_web_container.team_velocity_facade

    def populate_context(self, context, **kwargs):
        member_group_id = self.request.GET.get('member_group_id')
        use_custom_filter = self.request.GET.get('use_custom_filter') == 'true'

        context["month_sp"] = "{}"
        context["member_group_id"] = member_group_id or ''
        context["use_custom_filter"] = use_custom_filter
        context["has_custom_filter"] = self.team_velocity_facade.has_custom_filter(member_group_id)
        context["selected_period"] = self.request.GET.get('period', '')

        velocity_reports_data = asyncio.run(
            self.team_velocity_facade.get_velocity_reports_data(
                member_group_id, 12, use_custom_filter
            )
        )

        story_points_chart = self.team_velocity_facade.get_story_points_chart_data(velocity_reports_data)
        if story_points_chart and story_points_chart.labels:
            VelocitySortUtils.sort_chart_data_chronologically(story_points_chart)

        context["month_sp"] = ChartJsonUtils.convert_chart_data_to_chartjs_json(story_points_chart) if story_points_chart else "{}"
