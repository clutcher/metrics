from django.conf import settings

from .app.domain.model.config import (
    AzureRepoConfig, BitbucketConfig, PullRequestsConfig, ReviewGateConfig
)


def load_pull_requests_config() -> PullRequestsConfig:
    azure = AzureRepoConfig(
        organization_url=settings.METRICS_AZURE_ORGANIZATION_URL,
        pat=settings.METRICS_AZURE_PAT,
        project_keys=settings.METRICS_PROJECT_KEYS or []
    )

    bitbucket = BitbucketConfig(
        url=settings.METRICS_BITBUCKET_URL or None,
        workspace=settings.METRICS_BITBUCKET_WORKSPACE or None,
        username=settings.METRICS_BITBUCKET_USERNAME or None,
        app_password=settings.METRICS_BITBUCKET_APP_PASSWORD or None,
        repositories=settings.METRICS_BITBUCKET_REPOSITORIES or []
    )

    review_gate = ReviewGateConfig(
        main_reviewer_levels=settings.METRICS_PR_MAIN_REVIEWER_LEVELS,
        min_developer_approvals=settings.METRICS_PR_MIN_DEVELOPER_APPROVALS
    )

    return PullRequestsConfig(
        task_tracker=settings.METRICS_TASK_TRACKER,
        azure=azure,
        bitbucket=bitbucket,
        members=settings.METRICS_MEMBERS,
        seniority_levels=settings.METRICS_SENIORITY_LEVELS,
        review_gate=review_gate
    )
