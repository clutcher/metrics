import asyncio
import unittest

from pull_requests.app.domain.model.pull_request import (
    ApprovalVote, GatewayBlocker, GatewayState, PullRequestProjection, PullRequestRef, PullRequestSearchCriteria
)
from pull_requests.app.domain.model.review import PolicyEvaluationStatus, ReviewInputs
from pull_requests.tests.fixtures.pull_request_builders import detail_search_service, policy_evaluation, reviewer_vote

_ANY_REF = PullRequestRef(pull_request_id="1", repository_id="repo", project_id="proj", project_name="Project")


def gateway(review_inputs: ReviewInputs):
    service = detail_search_service(review_inputs)
    criteria = PullRequestSearchCriteria(target=_ANY_REF)
    pull_requests = asyncio.run(service.search(criteria, PullRequestProjection.REVIEW_DETAILS))
    return pull_requests[0].review.gateway


class TestPolicyGateway(unittest.TestCase):

    def test_shouldReportBlockedWithCiWhenBuildFailed(self):
        # given
        review_inputs = ReviewInputs(policy_evaluations=[policy_evaluation("build", PolicyEvaluationStatus.REJECTED)])

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual((GatewayState.BLOCKED, [GatewayBlocker.CI]), (result.state, result.blockers))

    def test_shouldReportBlockedWithChangesRequestedWhenAReviewerRejected(self):
        # given
        review_inputs = ReviewInputs(
            policy_evaluations=[policy_evaluation("reviewers", PolicyEvaluationStatus.REJECTED)],
            current_approvals=[reviewer_vote("dev-1", ApprovalVote.REJECTED)]
        )

        # when
        result = gateway(review_inputs)

        # then
        self.assertIn(GatewayBlocker.CHANGES_REQUESTED, result.blockers)

    def test_shouldReportBlockedWithChangesRequestedWhenAReviewerIsWaitingForAuthor(self):
        # given
        review_inputs = ReviewInputs(current_approvals=[reviewer_vote("dev-1", ApprovalVote.WAITING)])

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual((GatewayState.BLOCKED, [GatewayBlocker.CHANGES_REQUESTED]), (result.state, result.blockers))

    def test_shouldReportReadyWhenEveryBlockingPolicyApproved(self):
        # given
        review_inputs = ReviewInputs(policy_evaluations=[
            policy_evaluation("build", PolicyEvaluationStatus.APPROVED),
            policy_evaluation("reviewers", PolicyEvaluationStatus.APPROVED),
        ])

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual(GatewayState.READY, result.state)

    def test_shouldCountStaleButPreviouslyPassedBuildTowardReady(self):
        # given
        review_inputs = ReviewInputs(policy_evaluations=[
            policy_evaluation("reviewers", PolicyEvaluationStatus.APPROVED),
            policy_evaluation("build", PolicyEvaluationStatus.QUEUED, is_expired=True),
        ])

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual(GatewayState.READY, result.state)

    def test_shouldReportInReviewWhenBuildIsStillRunning(self):
        # given
        review_inputs = ReviewInputs(policy_evaluations=[
            policy_evaluation("reviewers", PolicyEvaluationStatus.APPROVED),
            policy_evaluation("build", PolicyEvaluationStatus.RUNNING),
        ])

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual(GatewayState.IN_REVIEW, result.state)

    def test_shouldReportInReviewWhenAwaitingReviewersWithoutAnyRejection(self):
        # given
        review_inputs = ReviewInputs(
            policy_evaluations=[policy_evaluation("reviewers", PolicyEvaluationStatus.REJECTED)],
            current_approvals=[reviewer_vote("dev-1", ApprovalVote.APPROVED)]
        )

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual(GatewayState.IN_REVIEW, result.state)

    def test_shouldReportInReviewWhenCommentsUnresolved(self):
        # given
        review_inputs = ReviewInputs(policy_evaluations=[
            policy_evaluation("build", PolicyEvaluationStatus.APPROVED),
            policy_evaluation("comments", PolicyEvaluationStatus.REJECTED),
        ])

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual(GatewayState.IN_REVIEW, result.state)

    def test_shouldReportInReviewWhenNoPoliciesConfigured(self):
        # given
        review_inputs = ReviewInputs()

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual(GatewayState.IN_REVIEW, result.state)

    def test_shouldReportBlockedWithMergeConflictWhenBranchHasConflicts(self):
        # given
        review_inputs = ReviewInputs(
            policy_evaluations=[policy_evaluation("build", PolicyEvaluationStatus.APPROVED)],
            has_merge_conflict=True
        )

        # when
        result = gateway(review_inputs)

        # then
        self.assertEqual((GatewayState.BLOCKED, [GatewayBlocker.MERGE_CONFLICT]), (result.state, result.blockers))


if __name__ == '__main__':
    unittest.main()
