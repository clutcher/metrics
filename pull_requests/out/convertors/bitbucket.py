from datetime import datetime
from typing import Any, Dict, List, Optional

from ...app.domain.model.pull_request import (
    Approval, ApprovalVote, Author, PullRequest, Reviewer, ReviewState
)
from .work_item_id_parser import WorkItemIdParser


class BitbucketPullRequestConverter:

    def convert_to_pull_request(self, raw_pull_request: Dict[str, Any], repository_name: Optional[str]) -> PullRequest:
        source_branch = self._extract_source_branch(raw_pull_request)
        title = raw_pull_request.get('title', '')

        return PullRequest(
            id=str(raw_pull_request.get('id', '')),
            title=title,
            author=self._convert_author(raw_pull_request.get('author')),
            status=raw_pull_request.get('state', ''),
            url=self._extract_url(raw_pull_request),
            repository=repository_name,
            repository_id=repository_name,
            source_branch=source_branch,
            is_draft=bool(raw_pull_request.get('draft', False)),
            created_date=self._parse_date(raw_pull_request.get('created_on')),
            review=ReviewState(approvals=self.convert_participants(raw_pull_request.get('participants'))),
            linked_task_id=WorkItemIdParser.parse_jira_issue_key(source_branch, title)
        )

    def convert_participants(self, participants: Optional[List[Dict[str, Any]]]) -> List[Approval]:
        if not participants:
            return []
        approvals = []
        for participant in participants:
            if participant.get('role') != 'REVIEWER':
                continue
            approvals.append(self._convert_participant(participant))
        return approvals

    def _convert_participant(self, participant: Dict[str, Any]) -> Approval:
        user = participant.get('user') or {}
        reviewer = Reviewer(
            id=user.get('account_id') or user.get('uuid') or user.get('display_name', ''),
            display_name=user.get('display_name', ''),
            is_required=False
        )
        return Approval(reviewer=reviewer, vote=self._convert_vote(participant))

    @staticmethod
    def _convert_vote(participant: Dict[str, Any]) -> ApprovalVote:
        state = participant.get('state')
        if state == 'approved' or participant.get('approved'):
            return ApprovalVote.APPROVED
        if state == 'changes_requested':
            return ApprovalVote.REJECTED
        return ApprovalVote.NO_VOTE

    @staticmethod
    def _convert_author(author: Optional[Dict[str, Any]]) -> Author:
        if not author:
            return Author(id='', display_name='')
        return Author(
            id=author.get('account_id') or author.get('uuid', ''),
            display_name=author.get('display_name', '')
        )

    @staticmethod
    def _extract_source_branch(raw_pull_request: Dict[str, Any]) -> Optional[str]:
        source = raw_pull_request.get('source') or {}
        branch = source.get('branch') or {}
        return branch.get('name')

    @staticmethod
    def _extract_url(raw_pull_request: Dict[str, Any]) -> Optional[str]:
        links = raw_pull_request.get('links') or {}
        html_link = links.get('html') or {}
        return html_link.get('href')

    @staticmethod
    def _parse_date(raw_date: Optional[str]) -> Optional[datetime]:
        if not raw_date:
            return None
        try:
            return datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
        except ValueError:
            return None
