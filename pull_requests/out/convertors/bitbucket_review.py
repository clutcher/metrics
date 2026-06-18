from datetime import datetime
from typing import Any, Dict, List, Optional

from ...app.domain.model.pull_request import Approval, ApprovalVote
from ...app.domain.model.review import (
    PolicyCategory, PolicyEvaluationStatus, RawPolicyEvaluation, ReviewInputs, VoteEvent
)
from .bitbucket import BitbucketPullRequestConverter

_APPROVAL_EVENT_KEY = "approval"
_CHANGES_REQUESTED_EVENT_KEY = "changes_requested"

_BUILD_STATUS_BY_STATE = {
    "SUCCESSFUL": PolicyEvaluationStatus.APPROVED,
    "INPROGRESS": PolicyEvaluationStatus.RUNNING,
    "FAILED": PolicyEvaluationStatus.REJECTED,
    "STOPPED": PolicyEvaluationStatus.REJECTED,
}


class BitbucketReviewConverter:

    def __init__(self):
        self._pull_request_converter = BitbucketPullRequestConverter()

    def to_review_inputs(self, participants: Optional[List[Dict[str, Any]]],
                         activity: Optional[List[Dict[str, Any]]],
                         build_statuses: Optional[List[Dict[str, Any]]]) -> ReviewInputs:
        return ReviewInputs(
            current_approvals=self._convert_current_approvals(participants),
            vote_events=self._convert_vote_events(activity),
            policy_evaluations=self._convert_build_evaluations(build_statuses)
        )

    def _convert_current_approvals(self, participants: Optional[List[Dict[str, Any]]]) -> List[Approval]:
        return self._pull_request_converter.convert_participants(participants)

    def _convert_vote_events(self, activity: Optional[List[Dict[str, Any]]]) -> List[VoteEvent]:
        if not activity:
            return []
        vote_events = []
        for entry in activity:
            vote_event = self._convert_vote_event(entry)
            if vote_event is not None:
                vote_events.append(vote_event)
        return vote_events

    def _convert_vote_event(self, entry: Dict[str, Any]) -> Optional[VoteEvent]:
        vote, payload = self._extract_vote(entry)
        if vote is None:
            return None
        reviewer_id, display_name = self._extract_voter(payload.get('user'))
        occurred_at = self._parse_date(payload.get('date'))
        if not reviewer_id or occurred_at is None:
            return None
        return VoteEvent(reviewer_id=reviewer_id, display_name=display_name, vote=vote, occurred_at=occurred_at)

    @staticmethod
    def _extract_vote(entry: Dict[str, Any]):
        if _APPROVAL_EVENT_KEY in entry:
            return ApprovalVote.APPROVED, entry[_APPROVAL_EVENT_KEY]
        if _CHANGES_REQUESTED_EVENT_KEY in entry:
            return ApprovalVote.REJECTED, entry[_CHANGES_REQUESTED_EVENT_KEY]
        return None, {}

    @staticmethod
    def _extract_voter(user: Optional[Dict[str, Any]]):
        user = user or {}
        reviewer_id = user.get('account_id') or user.get('uuid') or user.get('display_name')
        return reviewer_id, user.get('display_name', '')

    def _convert_build_evaluations(self, build_statuses: Optional[List[Dict[str, Any]]]) -> List[RawPolicyEvaluation]:
        if not build_statuses:
            return []
        evaluations = []
        for build_status in build_statuses:
            evaluation = self._convert_build_evaluation(build_status)
            if evaluation is not None:
                evaluations.append(evaluation)
        return evaluations

    @staticmethod
    def _convert_build_evaluation(build_status: Dict[str, Any]) -> Optional[RawPolicyEvaluation]:
        status = _BUILD_STATUS_BY_STATE.get(build_status.get('state'))
        if status is None:
            return None
        return RawPolicyEvaluation(
            type_id=build_status.get('key', '') or '',
            display_name=build_status.get('name', '') or build_status.get('key', '') or '',
            status=status,
            category=PolicyCategory.BUILD
        )

    @staticmethod
    def _parse_date(raw_date: Optional[str]) -> Optional[datetime]:
        if not raw_date:
            return None
        try:
            return datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
        except ValueError:
            return None
