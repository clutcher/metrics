import unittest

from ui_web.data.pull_request_data import ApprovalData, PullRequestData
from ui_web.utils.pull_request_summary_utils import PullRequestSummaryUtils


def approval(display_name: str, tier: str = "main") -> ApprovalData:
    return ApprovalData(display_name=display_name, state="approved", tier=tier, is_approval=True)


def change_request(display_name: str, tier: str = "main", state: str = "rejected") -> ApprovalData:
    return ApprovalData(display_name=display_name, state=state, tier=tier, is_approval=False)


def pull_request(*approvals: ApprovalData, author: str = "Author") -> PullRequestData:
    return PullRequestData(id="1", title="PR", author_name=author, status="active", approvals=list(approvals))


class TestPullRequestSummaryUtils(unittest.TestCase):

    def test_shouldCountHowManyPullRequestsEachPersonCreated(self):
        # given
        pull_requests = [
            pull_request(author="Stan"),
            pull_request(author="Stan"),
            pull_request(author="Gleb"),
        ]

        # when
        activity = PullRequestSummaryUtils.build_person_activity(pull_requests)

        # then
        self.assertEqual(2, next(person.created_count for person in activity if person.display_name == "Stan"))

    def test_shouldIncludeAuthorsWhoNeverReviewedAnyPullRequest(self):
        # given
        pull_requests = [pull_request(approval("Gleb"), author="Stan")]

        # when
        activity = PullRequestSummaryUtils.build_person_activity(pull_requests)

        # then
        stan = next(person for person in activity if person.display_name == "Stan")
        self.assertEqual((1, 0), (stan.created_count, stan.approved_count))

    def test_shouldCountHowManyPullRequestsEachReviewerApprovedAcrossTheList(self):
        # given
        pull_requests = [
            pull_request(approval("Gleb"), approval("Stan", tier="additional")),
            pull_request(approval("Gleb")),
        ]

        # when
        activity = PullRequestSummaryUtils.build_person_activity(pull_requests)

        # then
        self.assertEqual(2, next(person.approved_count for person in activity if person.display_name == "Gleb"))

    def test_shouldCountChangesRequestedSeparatelyFromApprovals(self):
        # given
        pull_requests = [
            pull_request(change_request("Andrey")),
            pull_request(approval("Andrey")),
        ]

        # when
        activity = PullRequestSummaryUtils.build_person_activity(pull_requests)

        # then
        andrey = next(person for person in activity if person.display_name == "Andrey")
        self.assertEqual((1, 1), (andrey.approved_count, andrey.changes_requested_count))

    def test_shouldCountWaitingForAuthorAsAChangesRequestedReview(self):
        # given
        pull_requests = [pull_request(change_request("Gleb", state="waiting"))]

        # when
        activity = PullRequestSummaryUtils.build_person_activity(pull_requests)

        # then
        gleb = next(person for person in activity if person.display_name == "Gleb")
        self.assertEqual(1, gleb.changes_requested_count)

    def test_shouldRankReviewersWithMostApprovalsFirst(self):
        # given
        pull_requests = [
            pull_request(approval("Gleb"), approval("Stan", tier="additional")),
            pull_request(approval("Gleb")),
        ]

        # when
        activity = PullRequestSummaryUtils.build_person_activity(pull_requests)

        # then
        self.assertEqual("Gleb", activity[0].display_name)


if __name__ == '__main__':
    unittest.main()
