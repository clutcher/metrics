from pull_requests.app.domain.model.pull_request import (
    Approval, ApprovalVote, Reviewer, ReviewTier
)


def approval(tier: ReviewTier, vote: ApprovalVote = ApprovalVote.APPROVED,
             reviewer_id: str = None, name: str = "Reviewer", is_required: bool = False) -> Approval:
    identifier = reviewer_id or f"{name}-{tier.value}"
    return Approval(
        reviewer=Reviewer(id=identifier, display_name=name, tier=tier, is_required=is_required),
        vote=vote
    )
