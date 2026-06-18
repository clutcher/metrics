import asyncio

from ..container import ui_web_container
from ..utils.pull_request_summary_utils import PullRequestSummaryUtils
from .graceful_template_view import GracefulTemplateView


class PullRequestsView(GracefulTemplateView):
    template_name = "pull_requests.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pull_requests_facade = ui_web_container.pull_requests_facade

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["partials/pull_requests_content.html"]
        return [self.template_name]

    def populate_context(self, context, **kwargs):
        context["pull_requests_enabled"] = self.pull_requests_facade.is_pull_requests_enabled()
        context["pull_requests"] = []
        context["success"] = False

        member_group_id = self.request.GET.get('member_group_id')
        context["selected_member_group_id"] = member_group_id
        pull_requests = asyncio.run(self.pull_requests_facade.get_pull_requests(member_group_id))
        context["pull_requests"] = pull_requests
        context["activity_summary"] = PullRequestSummaryUtils.build_person_activity(pull_requests)
        context["success"] = True
