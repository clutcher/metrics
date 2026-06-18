from typing import List

from ..model.pull_request import Approval, ReviewTier


class ReviewGateEvaluator:

    def __init__(self, min_developer_approvals: int):
        self._min_developer_approvals = min_developer_approvals

    def evaluate_internal_gate(self, approvals: List[Approval]) -> bool:
        distinct_additional_approvers = {
            approval.reviewer.id for approval in approvals
            if approval.reviewer.tier is ReviewTier.ADDITIONAL and approval.vote.is_positive
        }
        return len(distinct_additional_approvers) >= self._min_developer_approvals
