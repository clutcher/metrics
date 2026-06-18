import asyncio
import unittest

from pull_requests.app.domain.model.pull_request import (
    ApprovalVote, PullRequestProjection, PullRequestRef, PullRequestSearchCriteria
)
from pull_requests.app.domain.model.review import ReviewInputs
from pull_requests.tests.fixtures.pull_request_builders import detail_search_service, reviewer_vote, vote_event

_ANY_REF = PullRequestRef(pull_request_id="1", repository_id="repo", project_id="proj", project_name="Project")


def reset_approver_names(review_inputs: ReviewInputs) -> list:
    service = detail_search_service(review_inputs)
    criteria = PullRequestSearchCriteria(target=_ANY_REF)
    pull_requests = asyncio.run(service.search(criteria, PullRequestProjection.REVIEW_DETAILS))
    return [approval.reviewer.id for approval in pull_requests[0].review.reset_approvals]


class TestResetApprovalDetection(unittest.TestCase):

    def test_shouldFlagApprovalAsResetWhenReviewerApprovedThenLostVoteAfterNewCommit(self):
        # given
        review_inputs = ReviewInputs(
            current_approvals=[reviewer_vote("dev-1", ApprovalVote.NO_VOTE)],
            vote_events=[vote_event("dev-1", ApprovalVote.APPROVED, day=1)]
        )

        # when
        reset_reviewers = reset_approver_names(review_inputs)

        # then
        self.assertEqual(["dev-1"], reset_reviewers)

    def test_shouldNotFlagApprovalWhenReviewerStillApproves(self):
        # given
        review_inputs = ReviewInputs(
            current_approvals=[reviewer_vote("dev-1", ApprovalVote.APPROVED)],
            vote_events=[vote_event("dev-1", ApprovalVote.APPROVED, day=1)]
        )

        # when
        reset_reviewers = reset_approver_names(review_inputs)

        # then
        self.assertEqual([], reset_reviewers)

    def test_shouldNotFlagApprovalWhenReviewerReapprovedAfterTheNewCommit(self):
        # given
        review_inputs = ReviewInputs(
            current_approvals=[reviewer_vote("dev-1", ApprovalVote.APPROVED)],
            vote_events=[
                vote_event("dev-1", ApprovalVote.APPROVED, day=1),
                vote_event("dev-1", ApprovalVote.APPROVED, day=3),
            ]
        )

        # when
        reset_reviewers = reset_approver_names(review_inputs)

        # then
        self.assertEqual([], reset_reviewers)

    def test_shouldNotFlagApprovalWhenReviewerNeverApproved(self):
        # given
        review_inputs = ReviewInputs(
            current_approvals=[reviewer_vote("dev-1", ApprovalVote.WAITING)],
            vote_events=[vote_event("dev-1", ApprovalVote.WAITING, day=1)]
        )

        # when
        reset_reviewers = reset_approver_names(review_inputs)

        # then
        self.assertEqual([], reset_reviewers)


if __name__ == '__main__':
    unittest.main()
