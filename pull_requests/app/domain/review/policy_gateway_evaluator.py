from typing import List

from ..model.pull_request import Approval, ApprovalVote, GatewayBlocker, GatewayResult, GatewayState
from ..model.review import PolicyCategory, PolicyEvaluationStatus, RawPolicyEvaluation

_CATEGORY_BY_TYPE_ID = {
    "0609b952-1397-4640-95ec-e00a01b2c241": PolicyCategory.BUILD,
    "fa4e907d-c16b-4a4c-9dfa-4906e5d171dd": PolicyCategory.REVIEWERS,
    "fd2167ab-b0be-447a-8ec8-39368250530e": PolicyCategory.REVIEWERS,
    "c6a1889d-b943-4856-b76f-9e46bb6b0df2": PolicyCategory.COMMENTS,
    "40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e": PolicyCategory.WORK_ITEM,
    "cbdc66da-9728-4af8-aada-9a5a32e4a226": PolicyCategory.STATUS,
}

_CI_CATEGORIES = {PolicyCategory.BUILD, PolicyCategory.STATUS}
_CI_FAILURE_STATUSES = {PolicyEvaluationStatus.REJECTED, PolicyEvaluationStatus.BROKEN}
_CHANGES_REQUESTED_VOTES = {ApprovalVote.REJECTED, ApprovalVote.WAITING}


class PolicyGatewayEvaluator:

    def evaluate(self, policy_evaluations: List[RawPolicyEvaluation],
                 approvals: List[Approval]) -> GatewayResult:
        blockers = self._find_blockers(policy_evaluations, approvals)
        if blockers:
            return GatewayResult(state=GatewayState.BLOCKED, blockers=blockers)
        if policy_evaluations and all(self._is_satisfied(evaluation) for evaluation in policy_evaluations):
            return GatewayResult(state=GatewayState.READY)
        return GatewayResult(state=GatewayState.IN_REVIEW)

    def _find_blockers(self, policy_evaluations: List[RawPolicyEvaluation],
                       approvals: List[Approval]) -> List[GatewayBlocker]:
        blockers = []
        if any(self._is_ci_failure(evaluation) for evaluation in policy_evaluations):
            blockers.append(GatewayBlocker.CI)
        if any(approval.vote in _CHANGES_REQUESTED_VOTES for approval in approvals):
            blockers.append(GatewayBlocker.CHANGES_REQUESTED)
        return blockers

    def _is_ci_failure(self, evaluation: RawPolicyEvaluation) -> bool:
        return self._category(evaluation) in _CI_CATEGORIES and evaluation.status in _CI_FAILURE_STATUSES

    def _is_satisfied(self, evaluation: RawPolicyEvaluation) -> bool:
        if evaluation.status is PolicyEvaluationStatus.APPROVED:
            return True
        return self._is_stale_passed_build(evaluation)

    def _is_stale_passed_build(self, evaluation: RawPolicyEvaluation) -> bool:
        return (self._category(evaluation) is PolicyCategory.BUILD
                and evaluation.status is PolicyEvaluationStatus.QUEUED
                and evaluation.is_expired)

    @staticmethod
    def _category(evaluation: RawPolicyEvaluation) -> PolicyCategory:
        if evaluation.category is not None:
            return evaluation.category
        return _CATEGORY_BY_TYPE_ID.get((evaluation.type_id or "").lower(), PolicyCategory.OTHER)
