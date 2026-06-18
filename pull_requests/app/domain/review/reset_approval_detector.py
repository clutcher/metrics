from typing import Dict, List

from ..model.pull_request import Approval, ApprovalVote, Reviewer
from ..model.review import VoteEvent


class ResetApprovalDetector:

    def detect(self, current_approvals: List[Approval], vote_events: List[VoteEvent]) -> List[Approval]:
        current_vote_by_id = {approval.reviewer.id: approval.vote for approval in current_approvals}
        reviewer_by_id = {approval.reviewer.id: approval.reviewer for approval in current_approvals}
        latest_event_by_id = self._latest_event_per_reviewer(vote_events)

        reset_approvals = []
        for reviewer_id, event in latest_event_by_id.items():
            if not event.vote.is_positive:
                continue
            current_vote = current_vote_by_id.get(reviewer_id, ApprovalVote.NO_VOTE)
            if current_vote.is_positive:
                continue
            reviewer = reviewer_by_id.get(reviewer_id) or Reviewer(id=event.reviewer_id, display_name=event.display_name)
            reset_approvals.append(Approval(reviewer=reviewer, vote=event.vote))
        return reset_approvals

    @staticmethod
    def _latest_event_per_reviewer(vote_events: List[VoteEvent]) -> Dict[str, VoteEvent]:
        latest_event_by_id: Dict[str, VoteEvent] = {}
        for event in vote_events:
            existing = latest_event_by_id.get(event.reviewer_id)
            if existing is None or event.occurred_at > existing.occurred_at:
                latest_event_by_id[event.reviewer_id] = event
        return latest_event_by_id
