import unittest
from typing import List, Optional

from ui_web.data.pull_request_data import LinkedTaskData, PullRequestData
from ui_web.data.task_data import ReleaseData
from ui_web.utils.pull_request_filter_utils import PullRequestFilterUtils


def pull_request(author: str) -> PullRequestData:
    return PullRequestData(id="1", title="PR", author_name=author, status="active")


def pull_request_linked_to(iteration: Optional[str] = None,
                            releases: Optional[List[ReleaseData]] = None) -> PullRequestData:
    return PullRequestData(
        id="1", title="PR", author_name="Author", status="active",
        linked_task=LinkedTaskData(id="PROJ-1", iteration=iteration, releases=releases)
    )


def pull_request_without_linked_task() -> PullRequestData:
    return PullRequestData(id="1", title="PR", author_name="Author", status="active")


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


class TestPullRequestFilterUtilsIterationOptions(unittest.TestCase):

    def test_shouldListDistinctIterationsNaturallySortedWhenBuildingFilterOptions(self):
        # given
        pull_requests = [
            pull_request_linked_to(iteration="Sprint 10"),
            pull_request_linked_to(iteration="Sprint 2"),
            pull_request_linked_to(iteration="Sprint 2"),
        ]

        # when
        options = PullRequestFilterUtils.build_iteration_options(pull_requests)

        # then
        self.assertEqual(["Sprint 2", "Sprint 10"], options)

    def test_shouldSkipPullRequestsWithNoLinkedTicketOrNoIterationWhenBuildingFilterOptions(self):
        # given
        pull_requests = [pull_request_linked_to(iteration="Sprint 2"), pull_request_without_linked_task()]

        # when
        options = PullRequestFilterUtils.build_iteration_options(pull_requests)

        # then
        self.assertEqual(["Sprint 2"], options)


class TestPullRequestFilterUtilsIterationFiltering(unittest.TestCase):

    def test_shouldShowOnlyPullRequestsFromThatIterationWhenIterationSelected(self):
        # given
        pull_requests = [pull_request_linked_to(iteration="Sprint 2"), pull_request_linked_to(iteration="Sprint 3")]

        # when
        result = PullRequestFilterUtils.filter_by_iteration(pull_requests, "Sprint 2")

        # then
        self.assertEqual(["Sprint 2"], [pr.linked_task.iteration for pr in result])

    def test_shouldExcludePullRequestsWithoutLinkedTicketWhenIterationSelected(self):
        # given
        pull_requests = [pull_request_without_linked_task()]

        # when
        result = PullRequestFilterUtils.filter_by_iteration(pull_requests, "Sprint 2")

        # then
        self.assertEqual([], result)

    def test_shouldShowAllPullRequestsWhenNoIterationSelected(self):
        # given
        pull_requests = [pull_request_linked_to(iteration="Sprint 2"), pull_request_without_linked_task()]

        # when
        result = PullRequestFilterUtils.filter_by_iteration(pull_requests, None)

        # then
        self.assertEqual(pull_requests, result)


class TestPullRequestFilterUtilsReleaseOptions(unittest.TestCase):

    def test_shouldListDistinctReleasesNaturallySortedByNameWhenBuildingFilterOptions(self):
        # given
        pull_requests = [
            pull_request_linked_to(releases=[ReleaseData(id="rel-10", name="Release 10")]),
            pull_request_linked_to(releases=[ReleaseData(id="rel-2", name="Release 2")]),
        ]

        # when
        options = PullRequestFilterUtils.build_release_options(pull_requests)

        # then
        self.assertEqual([("rel-2", "Release 2"), ("rel-10", "Release 10")], options)

    def test_shouldDedupeSharedReleasesByIdWhenBuildingFilterOptions(self):
        # given
        pull_requests = [
            pull_request_linked_to(releases=[ReleaseData(id="rel-2", name="Release 2")]),
            pull_request_linked_to(releases=[ReleaseData(id="rel-2", name="Release 2")]),
        ]

        # when
        options = PullRequestFilterUtils.build_release_options(pull_requests)

        # then
        self.assertEqual([("rel-2", "Release 2")], options)

    def test_shouldSkipPullRequestsWithNoLinkedTicketOrNoReleasesWhenBuildingFilterOptions(self):
        # given
        pull_requests = [
            pull_request_linked_to(releases=[ReleaseData(id="rel-2", name="Release 2")]),
            pull_request_without_linked_task(),
        ]

        # when
        options = PullRequestFilterUtils.build_release_options(pull_requests)

        # then
        self.assertEqual([("rel-2", "Release 2")], options)


class TestPullRequestFilterUtilsReleaseFiltering(unittest.TestCase):

    def test_shouldShowOnlyPullRequestsForThatReleaseWhenReleaseSelected(self):
        # given
        pull_requests = [
            pull_request_linked_to(releases=[ReleaseData(id="rel-2", name="Release 2")]),
            pull_request_linked_to(releases=[ReleaseData(id="rel-3", name="Release 3")]),
        ]

        # when
        result = PullRequestFilterUtils.filter_by_release(pull_requests, "rel-2")

        # then
        self.assertEqual(["rel-2"], [release.id for pull_request in result for release in pull_request.linked_task.releases])

    def test_shouldMatchPullRequestWithMultipleReleasesWhenAnyReleaseMatchesSelection(self):
        # given
        pull_requests = [pull_request_linked_to(
            releases=[ReleaseData(id="rel-2", name="Release 2"), ReleaseData(id="rel-3", name="Release 3")]
        )]

        # when
        result = PullRequestFilterUtils.filter_by_release(pull_requests, "rel-3")

        # then
        self.assertEqual(["rel-2", "rel-3"], [release.id for release in result[0].linked_task.releases])

    def test_shouldExcludePullRequestsWithoutLinkedTicketWhenReleaseSelected(self):
        # given
        pull_requests = [pull_request_without_linked_task()]

        # when
        result = PullRequestFilterUtils.filter_by_release(pull_requests, "rel-2")

        # then
        self.assertEqual([], result)

    def test_shouldShowAllPullRequestsWhenNoReleaseSelected(self):
        # given
        pull_requests = [
            pull_request_linked_to(releases=[ReleaseData(id="rel-2", name="Release 2")]),
            pull_request_without_linked_task(),
        ]

        # when
        result = PullRequestFilterUtils.filter_by_release(pull_requests, None)

        # then
        self.assertEqual(pull_requests, result)


if __name__ == '__main__':
    unittest.main()
