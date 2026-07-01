import asyncio

from pull_requests.app.domain.model.pull_request import PullRequestRef
from ..container import ui_web_container
from ..utils.pull_request_filter_utils import PullRequestFilterUtils
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
        author_name = self.request.GET.get('author') or None
        context["selected_author"] = author_name

        pull_requests = asyncio.run(self.pull_requests_facade.get_pull_requests(member_group_id))
        context["author_options"] = PullRequestFilterUtils.build_author_options(pull_requests)
        pull_requests = PullRequestFilterUtils.filter_by_author(pull_requests, author_name)
        context["pull_requests"] = pull_requests
        context["activity_summary"] = PullRequestSummaryUtils.build_person_activity(pull_requests)
        context["success"] = True


class PullRequestReviewStateView(GracefulTemplateView):
    template_name = "partials/pull_request_review_state.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pull_requests_facade = ui_web_container.pull_requests_facade

    def populate_context(self, context, **kwargs):
        ref = self._build_ref(kwargs.get('pull_request_id'))
        context["pull_request"] = asyncio.run(self.pull_requests_facade.get_review_details(ref))
        context["success"] = True

    def _build_ref(self, pull_request_id):
        return PullRequestRef(
            pull_request_id=pull_request_id,
            repository_id=self.request.GET.get('repository_id', ''),
            project_id=self.request.GET.get('project_id', ''),
            project_name=self.request.GET.get('project', '')
        )
