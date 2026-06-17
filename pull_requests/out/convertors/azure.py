from typing import List, Optional

from ...app.domain.model.config import AzureRepoConfig
from ...app.domain.model.pull_request import (
    Approval, ApprovalVote, Author, PullRequest, Reviewer
)
from .work_item_id_parser import WorkItemIdParser

_VOTE_MAPPING = {
    10: ApprovalVote.APPROVED,
    5: ApprovalVote.APPROVED_WITH_SUGGESTIONS,
    0: ApprovalVote.NO_VOTE,
    -5: ApprovalVote.WAITING,
    -10: ApprovalVote.REJECTED,
}


class AzurePullRequestConverter:

    def __init__(self, azure_config: AzureRepoConfig):
        self._azure_config = azure_config

    def convert_to_pull_request(self, azure_pull_request) -> PullRequest:
        repository_name = self._extract_repository_name(azure_pull_request)
        project_name = self._extract_project_name(azure_pull_request)
        source_branch = azure_pull_request.source_ref_name

        return PullRequest(
            id=str(azure_pull_request.pull_request_id),
            title=azure_pull_request.title or '',
            author=self._convert_author(azure_pull_request.created_by),
            status=azure_pull_request.status or '',
            url=self._build_pull_request_url(project_name, repository_name, azure_pull_request.pull_request_id),
            repository=repository_name,
            source_branch=source_branch,
            is_draft=bool(azure_pull_request.is_draft),
            created_date=azure_pull_request.creation_date,
            approvals=self._convert_reviewers(azure_pull_request.reviewers),
            linked_task_id=WorkItemIdParser.parse_azure_work_item_id(source_branch, azure_pull_request.title)
        )

    def _convert_reviewers(self, azure_reviewers) -> List[Approval]:
        if not azure_reviewers:
            return []
        return [self._convert_reviewer(azure_reviewer) for azure_reviewer in azure_reviewers]

    @staticmethod
    def _convert_reviewer(azure_reviewer) -> Approval:
        reviewer = Reviewer(
            id=azure_reviewer.id or azure_reviewer.display_name or '',
            display_name=azure_reviewer.display_name or '',
            is_required=bool(getattr(azure_reviewer, 'is_required', False))
        )
        vote = _VOTE_MAPPING.get(azure_reviewer.vote or 0, ApprovalVote.NO_VOTE)
        return Approval(reviewer=reviewer, vote=vote)

    @staticmethod
    def _convert_author(created_by) -> Author:
        if not created_by:
            return Author(id='', display_name='')
        return Author(id=created_by.id or '', display_name=created_by.display_name or '')

    @staticmethod
    def _extract_repository_name(azure_pull_request) -> Optional[str]:
        repository = azure_pull_request.repository
        return repository.name if repository else None

    @staticmethod
    def _extract_project_name(azure_pull_request) -> Optional[str]:
        repository = azure_pull_request.repository
        if repository and repository.project:
            return repository.project.name
        return None

    def _build_pull_request_url(self, project_name: Optional[str], repository_name: Optional[str],
                                pull_request_id: int) -> Optional[str]:
        if not all([self._azure_config.organization_url, project_name, repository_name]):
            return None
        base_url = self._azure_config.organization_url.rstrip('/')
        return f"{base_url}/{project_name}/_git/{repository_name}/pullrequest/{pull_request_id}"
