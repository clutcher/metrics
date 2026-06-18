from .app.api.api_for_pull_request_search import ApiForPullRequestSearch
from .app.domain.pull_request_search_service import PullRequestSearchService
from .app.domain.review.policy_gateway_evaluator import PolicyGatewayEvaluator
from .app.domain.review.pull_request_review_enricher import PullRequestReviewEnricher
from .app.domain.review.reset_approval_detector import ResetApprovalDetector
from .app.domain.review.review_gate_evaluator import ReviewGateEvaluator
from .app.domain.review.reviewer_seniority import ReviewerSeniority
from .app.spi.pull_request_repository import PullRequestRepository
from .config_loader import load_pull_requests_config
from .out.azure_pull_request_repository import AzurePullRequestRepository
from .out.bitbucket_pull_request_repository import BitbucketPullRequestRepository


class PullRequestsContainer:

    def __init__(self):
        self._config = load_pull_requests_config()
        self._repository = None
        self._service = None

    @property
    def pull_request_search_api(self) -> ApiForPullRequestSearch:
        if self._service is None:
            self._service = PullRequestSearchService(
                repository=self._get_repository(),
                review_enricher=self._build_review_enricher()
            )
        return self._service

    def _build_review_enricher(self) -> PullRequestReviewEnricher:
        return PullRequestReviewEnricher(
            reviewer_seniority=self._build_reviewer_seniority(),
            review_gate_evaluator=self._build_review_gate_evaluator(),
            reset_approval_detector=ResetApprovalDetector(),
            policy_gateway_evaluator=PolicyGatewayEvaluator()
        )

    def is_supported(self) -> bool:
        if self._config.is_azure_tracker():
            return self._config.is_azure_configured()
        if self._config.is_jira_tracker():
            return self._config.is_bitbucket_configured()
        return False

    def _get_repository(self) -> PullRequestRepository:
        if self._repository is None:
            self._repository = self._create_repository()
        return self._repository

    def _create_repository(self) -> PullRequestRepository:
        if self._config.is_azure_tracker():
            return AzurePullRequestRepository(self._config)
        if self._config.is_jira_tracker():
            return BitbucketPullRequestRepository(self._config)
        raise ValueError("Pull request data source not configured.")

    def _build_reviewer_seniority(self) -> ReviewerSeniority:
        return ReviewerSeniority(
            members=self._config.members,
            main_reviewer_levels=self._config.review_gate.main_reviewer_levels,
            seniority_levels=self._config.seniority_levels
        )

    def _build_review_gate_evaluator(self) -> ReviewGateEvaluator:
        return ReviewGateEvaluator(self._config.review_gate.min_developer_approvals)


pull_requests_container = PullRequestsContainer()
