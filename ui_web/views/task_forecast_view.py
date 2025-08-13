import asyncio

from django.views.generic import TemplateView

from ..container import ui_web_container
from ..utils.chart_json_utils import ChartJsonUtils


class TaskForecastView(TemplateView):
    template_name = 'task_forecast.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.task_forecast_facade = ui_web_container.task_forecast_facade
        self.task_forecast_convertor = ui_web_container.task_forecast_convertor

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["partials/task_forecast_content.html"]
        return [self.template_name]

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request_data = self.task_forecast_convertor.extract_request_data_from_request(self.request)

        try:
            forecast_params = asyncio.run(self.task_forecast_facade.get_forecast_params_data(request_data))
            context["forecast_params"] = forecast_params

            if request_data.task_id:
                task_hierarchy = asyncio.run(self.task_forecast_facade.get_task_forecast_hierarchy_data(request_data))
                forecast_chart = self.task_forecast_facade.get_forecast_chart_from_data(task_hierarchy)

                context["task_breakdown"] = task_hierarchy
                context["task_forecast"] = self.task_forecast_facade.get_forecast_summary_from_data(task_hierarchy)
                context["chart_data"] = ChartJsonUtils.convert_chart_data_to_timeline_chartjs_json(
                    forecast_chart) if forecast_chart else ""

            context["success"] = True
        except Exception as e:
            context["forecast_params"] = None
            context["task_forecast"] = None
            context["chart_data"] = ""
            context["task_breakdown"] = []
            context["success"] = False
            context["error"] = str(e)

        return context
