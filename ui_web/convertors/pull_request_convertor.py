from typing import List, Optional

from pull_requests.app.domain.model.pull_request import Approval, ApprovalVote, PullRequest
from tasks.app.domain.model.task import Task
from ..data.pull_request_data import ApprovalData, LinkedTaskData, PullRequestData


class PullRequestConvertor:

    def convert_to_data(self, pull_request: PullRequest, linked_task: Optional[Task]) -> PullRequestData:
        return PullRequestData(
            id=pull_request.id,
            title=pull_request.title,
            author_name=pull_request.author.display_name,
            status=pull_request.status,
            internal_gate=pull_request.internal_gate_met,
            required_gate=pull_request.required_gate_met,
            url=pull_request.url,
            repository=pull_request.repository,
            is_draft=pull_request.is_draft,
            approvals=self._convert_visible_approvals(pull_request.approvals),
            linked_task=self._convert_linked_task(pull_request.linked_task_id, linked_task)
        )

    @staticmethod
    def _convert_visible_approvals(approvals: List[Approval]) -> List[ApprovalData]:
        visible_approvals = []
        for approval in approvals:
            if approval.vote is ApprovalVote.NO_VOTE:
                continue
            visible_approvals.append(ApprovalData(
                display_name=approval.reviewer.display_name,
                state=approval.vote.value,
                tier=approval.reviewer.tier.value,
                is_approval=approval.vote.is_positive
            ))
        return visible_approvals

    @staticmethod
    def _convert_linked_task(linked_task_id: Optional[str], linked_task: Optional[Task]) -> Optional[LinkedTaskData]:
        if not linked_task_id:
            return None
        if linked_task:
            return LinkedTaskData(
                id=linked_task.id,
                url=linked_task.system_metadata.url if linked_task.system_metadata else None
            )
        return LinkedTaskData(id=linked_task_id)
