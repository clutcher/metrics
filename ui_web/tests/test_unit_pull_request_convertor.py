import unittest

from pull_requests.app.domain.model.pull_request import (
    Author, GatewayBlocker, GatewayResult, GatewayState, PullRequest, ReviewState
)
from ui_web.convertors.pull_request_convertor import PullRequestConvertor


def pull_request_with_gateway(gateway: GatewayResult) -> PullRequest:
    return PullRequest(
        id="1", title="Improve checkout", author=Author(id="a", display_name="Author"),
        status="active", review=ReviewState(gateway=gateway)
    )


class TestGatewayDisplay(unittest.TestCase):

    def test_shouldShowSingleGreenReadyChipWhenGatewayIsReady(self):
        # given
        pull_request = pull_request_with_gateway(GatewayResult(state=GatewayState.READY))

        # when
        policies = PullRequestConvertor().convert_review_details(pull_request).policies

        # then
        self.assertEqual([("Ready", "is-success")], [(policy.name, policy.css_class) for policy in policies])

    def test_shouldShowOneRedChipPerBlockerWhenGatewayIsBlocked(self):
        # given
        pull_request = pull_request_with_gateway(GatewayResult(
            state=GatewayState.BLOCKED,
            blockers=[GatewayBlocker.CI, GatewayBlocker.CHANGES_REQUESTED]
        ))

        # when
        policies = PullRequestConvertor().convert_review_details(pull_request).policies

        # then
        self.assertEqual(["CI", "Changes requested"], [policy.name for policy in policies])

    def test_shouldMarkBlockerChipsAsDangerWhenGatewayIsBlocked(self):
        # given
        pull_request = pull_request_with_gateway(GatewayResult(state=GatewayState.BLOCKED, blockers=[GatewayBlocker.CI]))

        # when
        policies = PullRequestConvertor().convert_review_details(pull_request).policies

        # then
        self.assertEqual("is-danger", policies[0].css_class)

    def test_shouldShowMutedInReviewChipWhenGatewayIsInReview(self):
        # given
        pull_request = pull_request_with_gateway(GatewayResult(state=GatewayState.IN_REVIEW))

        # when
        policies = PullRequestConvertor().convert_review_details(pull_request).policies

        # then
        self.assertEqual([("In review", "is-light has-text-grey")], [(policy.name, policy.css_class) for policy in policies])

    def test_shouldShowNoPolicyChipsWhenGatewayIsUnknown(self):
        # given
        pull_request = pull_request_with_gateway(None)

        # when
        policies = PullRequestConvertor().convert_review_details(pull_request).policies

        # then
        self.assertEqual([], policies)


if __name__ == '__main__':
    unittest.main()
