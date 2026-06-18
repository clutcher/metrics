from typing import Any, List, Optional, Tuple

from ...app.domain.model.pull_request import Approval, ApprovalVote, Reviewer
from ...app.domain.model.review import (
    PolicyEvaluationStatus, RawPolicyEvaluation, ReviewInputs, VoteEvent
)
from .azure import _VOTE_MAPPING

_VOTE_UPDATE_THREAD_TYPE = "VoteUpdate"
_THREAD_TYPE_PROPERTY = "CodeReviewThreadType"
_VOTE_RESULT_PROPERTY = "CodeReviewVoteResult"

_POLICY_STATUS_BY_VALUE = {status.value: status for status in PolicyEvaluationStatus}


class AzureReviewConverter:

    def to_review_inputs(self, azure_reviewers, azure_threads, azure_policy_evaluations) -> ReviewInputs:
        return ReviewInputs(
            current_approvals=self._convert_current_approvals(azure_reviewers),
            vote_events=self._convert_vote_events(azure_threads),
            policy_evaluations=self._convert_policy_evaluations(azure_policy_evaluations)
        )

    def _convert_current_approvals(self, azure_reviewers) -> List[Approval]:
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

    def _convert_vote_events(self, azure_threads) -> List[VoteEvent]:
        if not azure_threads:
            return []
        vote_events = []
        for thread in azure_threads:
            vote_event = self._convert_vote_event(thread)
            if vote_event is not None:
                vote_events.append(vote_event)
        return vote_events

    def _convert_vote_event(self, thread) -> Optional[VoteEvent]:
        properties = getattr(thread, 'properties', None)
        if self._property_value(properties, _THREAD_TYPE_PROPERTY) != _VOTE_UPDATE_THREAD_TYPE:
            return None

        raw_vote = self._property_value(properties, _VOTE_RESULT_PROPERTY)
        if raw_vote is None:
            return None
        vote = _VOTE_MAPPING.get(int(raw_vote), ApprovalVote.NO_VOTE)

        reviewer_id, display_name = self._extract_voter(thread)
        occurred_at = getattr(thread, 'published_date', None) or getattr(thread, 'last_updated_date', None)
        if not reviewer_id or occurred_at is None:
            return None

        return VoteEvent(reviewer_id=reviewer_id, display_name=display_name, vote=vote, occurred_at=occurred_at)

    def _extract_voter(self, thread) -> Tuple[Optional[str], str]:
        identities = getattr(thread, 'identities', None)
        if isinstance(identities, dict):
            for identity in identities.values():
                identity_id, display_name = self._identity_fields(identity)
                if identity_id:
                    return identity_id, display_name
        return None, ''

    @staticmethod
    def _identity_fields(identity: Any) -> Tuple[Optional[str], str]:
        if isinstance(identity, dict):
            return identity.get('id'), identity.get('displayName') or ''
        return getattr(identity, 'id', None), getattr(identity, 'display_name', '') or ''

    def _convert_policy_evaluations(self, azure_policy_evaluations) -> List[RawPolicyEvaluation]:
        if not azure_policy_evaluations:
            return []
        evaluations = []
        for evaluation in azure_policy_evaluations:
            converted = self._convert_policy_evaluation(evaluation)
            if converted is not None:
                evaluations.append(converted)
        return evaluations

    def _convert_policy_evaluation(self, evaluation) -> Optional[RawPolicyEvaluation]:
        configuration = getattr(evaluation, 'configuration', None)
        if configuration is None or not self._is_authoritative(configuration):
            return None
        policy_type = getattr(configuration, 'type', None)
        if policy_type is None:
            return None
        status = _POLICY_STATUS_BY_VALUE.get(getattr(evaluation, 'status', None))
        if status is None:
            return None
        return RawPolicyEvaluation(
            type_id=getattr(policy_type, 'id', '') or '',
            display_name=getattr(policy_type, 'display_name', '') or '',
            status=status,
            is_expired=self._is_expired(evaluation)
        )

    @staticmethod
    def _is_expired(evaluation) -> bool:
        context = getattr(evaluation, 'context', None) or {}
        return bool(context.get('isExpired')) if isinstance(context, dict) else False

    @staticmethod
    def _is_authoritative(configuration) -> bool:
        return (getattr(configuration, 'is_blocking', True)
                and getattr(configuration, 'is_enabled', True)
                and not getattr(configuration, 'is_deleted', False))

    @staticmethod
    def _property_value(properties, key: str):
        if not properties:
            return None
        entry = properties.get(key)
        if isinstance(entry, dict):
            return entry.get('$value')
        return entry
