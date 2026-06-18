import unittest

from pull_requests.app.domain.model.pull_request import GatewayBlocker, GatewayState
from pull_requests.app.domain.model.review import (
    PolicyCategory, PolicyEvaluationStatus, RawPolicyEvaluation
)
from pull_requests.app.domain.review.policy_gateway_evaluator import PolicyGatewayEvaluator


def build_evaluation(status: PolicyEvaluationStatus) -> RawPolicyEvaluation:
    return RawPolicyEvaluation(
        type_id="pipeline", display_name="Pipeline", status=status, category=PolicyCategory.BUILD
    )


class TestPolicyGatewayEvaluatorHonorsCategory(unittest.TestCase):

    def test_shouldBlockWithCiWhenCategorisedBuildFailedWithoutAzureTypeId(self):
        # given
        evaluations = [build_evaluation(PolicyEvaluationStatus.REJECTED)]

        # when
        result = PolicyGatewayEvaluator().evaluate(evaluations, [])

        # then
        self.assertEqual((GatewayState.BLOCKED, [GatewayBlocker.CI]), (result.state, result.blockers))

    def test_shouldReportReadyWhenCategorisedBuildApprovedWithoutAzureTypeId(self):
        # given
        evaluations = [build_evaluation(PolicyEvaluationStatus.APPROVED)]

        # when
        result = PolicyGatewayEvaluator().evaluate(evaluations, [])

        # then
        self.assertEqual(GatewayState.READY, result.state)


if __name__ == '__main__':
    unittest.main()
