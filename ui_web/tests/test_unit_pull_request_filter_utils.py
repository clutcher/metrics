import unittest

from ui_web.data.pull_request_data import PullRequestData
from ui_web.utils.pull_request_filter_utils import PullRequestFilterUtils


def pull_request(author: str) -> PullRequestData:
    return PullRequestData(id="1", title="PR", author_name=author, status="active")


class TestPullRequestFilterUtilsAuthorOptions(unittest.TestCase):

    def test_shouldListDistinctAuthorsAlphabeticallyWhenBuildingFilterOptions(self):
        # given
        pull_requests = [pull_request("Stan"), pull_request("Gleb"), pull_request("Stan")]

        # when
        options = PullRequestFilterUtils.build_author_options(pull_requests)

        # then
        self.assertEqual(["Gleb", "Stan"], options)


class TestPullRequestFilterUtilsAuthorFiltering(unittest.TestCase):

    def test_shouldShowOnlyThatAuthorsPullRequestsWhenAuthorSelected(self):
        # given
        pull_requests = [pull_request("Stan"), pull_request("Gleb")]

        # when
        result = PullRequestFilterUtils.filter_by_author(pull_requests, "Gleb")

        # then
        self.assertEqual(["Gleb"], [pull_request.author_name for pull_request in result])

    def test_shouldKeepReviewedPullRequestsOutWhenAuthorSelectedButOnlyReviewedThem(self):
        # given
        pull_requests = [pull_request("Stan")]

        # when
        result = PullRequestFilterUtils.filter_by_author(pull_requests, "Gleb")

        # then
        self.assertEqual([], result)

    def test_shouldShowAllPullRequestsWhenNoAuthorSelected(self):
        # given
        pull_requests = [pull_request("Stan"), pull_request("Gleb")]

        # when
        result = PullRequestFilterUtils.filter_by_author(pull_requests, None)

        # then
        self.assertEqual(pull_requests, result)


if __name__ == '__main__':
    unittest.main()
