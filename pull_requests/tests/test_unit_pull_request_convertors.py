import unittest
from types import SimpleNamespace

from pull_requests.app.domain.model.config import AzureRepoConfig
from pull_requests.app.domain.model.pull_request import ApprovalVote
from pull_requests.out.convertors.azure import AzurePullRequestConverter
from pull_requests.out.convertors.bitbucket import BitbucketPullRequestConverter
from pull_requests.out.convertors.work_item_id_parser import WorkItemIdParser


def azure_config() -> AzureRepoConfig:
    return AzureRepoConfig(
        organization_url="https://dev.azure.com/Org",
        pat="secret",
        project_keys=["Payments"]
    )


def azure_reviewer(display_name: str, vote: int):
    return SimpleNamespace(id=display_name, display_name=display_name, vote=vote, is_required=True)


def azure_pull_request(reviewers, source_ref_name="refs/heads/feature/4821-checkout", title="Improve checkout"):
    return SimpleNamespace(
        pull_request_id=17,
        title=title,
        created_by=SimpleNamespace(id="u1", display_name="Author"),
        status="active",
        is_draft=False,
        creation_date=None,
        source_ref_name=source_ref_name,
        reviewers=reviewers,
        repository=SimpleNamespace(name="checkout-service", project=SimpleNamespace(name="Payments"))
    )


class TestAzurePullRequestConverter(unittest.TestCase):

    def test_shouldTranslateAzureApprovalVoteIntoApprovedDecision(self):
        # given
        pull_request = azure_pull_request([azure_reviewer("Lena Lead", 10)])

        # when
        converted = AzurePullRequestConverter(azure_config()).convert_to_pull_request(pull_request)

        # then
        self.assertEqual(ApprovalVote.APPROVED, converted.review.approvals[0].vote)

    def test_shouldTranslateAzureRejectionVoteIntoChangesRequestedDecision(self):
        # given
        pull_request = azure_pull_request([azure_reviewer("Dave Developer", -10)])

        # when
        converted = AzurePullRequestConverter(azure_config()).convert_to_pull_request(pull_request)

        # then
        self.assertEqual(ApprovalVote.REJECTED, converted.review.approvals[0].vote)

    def test_shouldLinkPullRequestToWorkItemParsedFromSourceBranch(self):
        # given
        pull_request = azure_pull_request([], source_ref_name="refs/heads/feature/4821-checkout")

        # when
        converted = AzurePullRequestConverter(azure_config()).convert_to_pull_request(pull_request)

        # then
        self.assertEqual("4821", converted.linked_task_id)

    def test_shouldBuildWebUrlPointingToThePullRequestInAzureRepos(self):
        # given
        pull_request = azure_pull_request([])

        # when
        converted = AzurePullRequestConverter(azure_config()).convert_to_pull_request(pull_request)

        # then
        self.assertEqual(
            "https://dev.azure.com/Org/Payments/_git/checkout-service/pullrequest/17",
            converted.url
        )


class TestBitbucketPullRequestConverter(unittest.TestCase):

    def test_shouldTranslateBitbucketApprovedParticipantIntoApprovedDecision(self):
        # given
        raw_pull_request = {
            "id": 42,
            "title": "Fix PROJ-19 login",
            "state": "OPEN",
            "author": {"display_name": "Author", "account_id": "a1"},
            "source": {"branch": {"name": "feature/PROJ-19-login"}},
            "participants": [
                {"role": "REVIEWER", "approved": True, "state": "approved",
                 "user": {"display_name": "Lena Lead", "account_id": "r1"}}
            ]
        }

        # when
        converted = BitbucketPullRequestConverter().convert_to_pull_request(raw_pull_request, "web")

        # then
        self.assertEqual(ApprovalVote.APPROVED, converted.review.approvals[0].vote)

    def test_shouldTranslateBitbucketChangesRequestedParticipantIntoRejection(self):
        # given
        raw_pull_request = {
            "id": 42,
            "title": "Fix login",
            "state": "OPEN",
            "source": {"branch": {"name": "feature/PROJ-19-login"}},
            "participants": [
                {"role": "REVIEWER", "approved": False, "state": "changes_requested",
                 "user": {"display_name": "Dave Developer", "account_id": "r2"}}
            ]
        }

        # when
        converted = BitbucketPullRequestConverter().convert_to_pull_request(raw_pull_request, "web")

        # then
        self.assertEqual(ApprovalVote.REJECTED, converted.review.approvals[0].vote)

    def test_shouldLinkPullRequestToJiraIssueParsedFromSourceBranch(self):
        # given
        raw_pull_request = {
            "id": 42,
            "title": "Login work",
            "state": "OPEN",
            "source": {"branch": {"name": "feature/PROJ-19-login"}},
            "participants": []
        }

        # when
        converted = BitbucketPullRequestConverter().convert_to_pull_request(raw_pull_request, "web")

        # then
        self.assertEqual("PROJ-19", converted.linked_task_id)


class TestWorkItemIdParser(unittest.TestCase):

    def test_shouldPreferExplicitAzureWorkItemMentionInTitleOverBranchNumber(self):
        # given # when
        work_item_id = WorkItemIdParser.parse_azure_work_item_id(
            "refs/heads/feature/4821-checkout", "Improve checkout AB#9001"
        )

        # then
        self.assertEqual("9001", work_item_id)

    def test_shouldReturnNoWorkItemWhenBranchAndTitleHaveNoIdentifier(self):
        # given # when
        work_item_id = WorkItemIdParser.parse_azure_work_item_id("refs/heads/cleanup", "Tidy up")

        # then
        self.assertIsNone(work_item_id)

    def test_shouldParseJiraIssueKeyFromTitleWhenBranchHasNone(self):
        # given # when
        issue_key = WorkItemIdParser.parse_jira_issue_key("refs/heads/cleanup", "Resolve PROJ-77 crash")

        # then
        self.assertEqual("PROJ-77", issue_key)


if __name__ == '__main__':
    unittest.main()
