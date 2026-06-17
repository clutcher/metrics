import unittest

from pull_requests.app.domain.model.pull_request import ApprovalVote, ReviewTier
from pull_requests.app.domain.review.review_gate_evaluator import ReviewGateEvaluator
from pull_requests.tests.fixtures.pull_request_builders import approval


def evaluator(min_developer_approvals: int = 2) -> ReviewGateEvaluator:
    return ReviewGateEvaluator(min_developer_approvals=min_developer_approvals)


class TestInternalGate(unittest.TestCase):

    def test_shouldNotPassInternalGateWhenFewerThanTwoAdditionalReviewersApproved(self):
        # given
        approvals = [approval(ReviewTier.ADDITIONAL, reviewer_id="dev-1")]

        # when
        internal_gate_met = evaluator().evaluate_internal_gate(approvals)

        # then
        self.assertFalse(internal_gate_met)

    def test_shouldPassInternalGateWhenTwoAdditionalReviewersApproved(self):
        # given
        approvals = [
            approval(ReviewTier.ADDITIONAL, reviewer_id="dev-1"),
            approval(ReviewTier.ADDITIONAL, reviewer_id="dev-2"),
        ]

        # when
        internal_gate_met = evaluator().evaluate_internal_gate(approvals)

        # then
        self.assertTrue(internal_gate_met)

    def test_shouldNotCountMainReviewersTowardsTheInternalGate(self):
        # given
        approvals = [
            approval(ReviewTier.MAIN, reviewer_id="lead-1"),
            approval(ReviewTier.MAIN, reviewer_id="arch-1"),
        ]

        # when
        internal_gate_met = evaluator().evaluate_internal_gate(approvals)

        # then
        self.assertFalse(internal_gate_met)

    def test_shouldOnlyCountPositiveVotesTowardTheInternalGate(self):
        # given
        approvals = [
            approval(ReviewTier.ADDITIONAL, reviewer_id="dev-1"),
            approval(ReviewTier.ADDITIONAL, vote=ApprovalVote.WAITING, reviewer_id="dev-2"),
        ]

        # when
        internal_gate_met = evaluator().evaluate_internal_gate(approvals)

        # then
        self.assertFalse(internal_gate_met)


class TestRequiredGate(unittest.TestCase):

    def test_shouldBeNotApplicableWhenPullRequestHasNoRequiredReviewers(self):
        # given
        approvals = [approval(ReviewTier.ADDITIONAL, reviewer_id="dev-1")]

        # when
        required_gate_met = evaluator().evaluate_required_gate(approvals)

        # then
        self.assertIsNone(required_gate_met)

    def test_shouldPassRequiredGateWhenTheSoleRequiredReviewerApprovedAlone(self):
        # given
        approvals = [approval(ReviewTier.MAIN, reviewer_id="arch-1", is_required=True)]

        # when
        required_gate_met = evaluator().evaluate_required_gate(approvals)

        # then
        self.assertTrue(required_gate_met)

    def test_shouldFailRequiredGateWhenARequiredReviewerHasNotApprovedDespiteManyOtherApprovals(self):
        # given
        approvals = [
            approval(ReviewTier.MAIN, vote=ApprovalVote.WAITING, reviewer_id="arch-1", is_required=True),
            approval(ReviewTier.ADDITIONAL, reviewer_id="dev-1"),
            approval(ReviewTier.ADDITIONAL, reviewer_id="dev-2"),
            approval(ReviewTier.ADDITIONAL, reviewer_id="dev-3"),
        ]

        # when
        required_gate_met = evaluator().evaluate_required_gate(approvals)

        # then
        self.assertFalse(required_gate_met)

    def test_shouldFailRequiredGateWhenARequiredReviewerRejected(self):
        # given
        approvals = [approval(ReviewTier.MAIN, vote=ApprovalVote.REJECTED, reviewer_id="arch-1", is_required=True)]

        # when
        required_gate_met = evaluator().evaluate_required_gate(approvals)

        # then
        self.assertFalse(required_gate_met)


if __name__ == '__main__':
    unittest.main()
