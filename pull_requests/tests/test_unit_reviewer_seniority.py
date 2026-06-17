import unittest

from pull_requests.app.domain.model.pull_request import Reviewer, ReviewTier
from pull_requests.app.domain.review.reviewer_seniority import ReviewerSeniority

MEMBERS = {
    "Anna Architect": {"level": "arch"},
    "Lena Lead": {"level": "lead"},
    "Dave Developer": {"level": "senior"},
    "Mia Middle": {"level": "middle"},
}

SENIORITY_LEVELS = {"arch": 1.0, "lead": 1.0, "senior": 1.0, "middle": 2.0, "junior": 4.0}


def reviewer_seniority() -> ReviewerSeniority:
    return ReviewerSeniority(
        members=MEMBERS,
        main_reviewer_levels=["lead", "arch"],
        seniority_levels=SENIORITY_LEVELS
    )


class TestReviewerSeniorityTierClassification(unittest.TestCase):

    def test_shouldClassifyMemberAsMainReviewerWhenLevelIsArchitect(self):
        # given # when
        tier = reviewer_seniority().resolve_tier("Anna Architect")

        # then
        self.assertEqual(ReviewTier.MAIN, tier)

    def test_shouldClassifyMemberAsMainReviewerWhenLevelIsLead(self):
        # given # when
        tier = reviewer_seniority().resolve_tier("Lena Lead")

        # then
        self.assertEqual(ReviewTier.MAIN, tier)

    def test_shouldClassifyMemberAsAdditionalReviewerWhenLevelIsNotConfiguredAsMain(self):
        # given # when
        tier = reviewer_seniority().resolve_tier("Dave Developer")

        # then
        self.assertEqual(ReviewTier.ADDITIONAL, tier)

    def test_shouldClassifyReviewerAsAdditionalWhenNotInTeamConfiguration(self):
        # given # when
        tier = reviewer_seniority().resolve_tier("External Contributor")

        # then
        self.assertEqual(ReviewTier.ADDITIONAL, tier)


class TestReviewerSeniorityApprovalOrdering(unittest.TestCase):

    def test_shouldOrderMainReviewerFirstWhenSortingAgainstAnAdditionalReviewer(self):
        # given
        main_reviewer = Reviewer(id="1", display_name="Lena", tier=ReviewTier.MAIN, level="lead")
        additional_reviewer = Reviewer(id="2", display_name="Dave", tier=ReviewTier.ADDITIONAL, level="senior")

        # when
        ordered = sorted([additional_reviewer, main_reviewer], key=reviewer_seniority().approval_sort_key)

        # then
        self.assertEqual([main_reviewer, additional_reviewer], ordered)

    def test_shouldOrderSeniorReviewerFirstWhenSortingAdditionalReviewersBySeniority(self):
        # given
        senior_reviewer = Reviewer(id="1", display_name="Dave", tier=ReviewTier.ADDITIONAL, level="senior")
        middle_reviewer = Reviewer(id="2", display_name="Mia", tier=ReviewTier.ADDITIONAL, level="middle")

        # when
        ordered = sorted([middle_reviewer, senior_reviewer], key=reviewer_seniority().approval_sort_key)

        # then
        self.assertEqual([senior_reviewer, middle_reviewer], ordered)

    def test_shouldPlaceReviewerLastWhenTheirLevelIsUnknown(self):
        # given
        known_reviewer = Reviewer(id="1", display_name="Dave", tier=ReviewTier.ADDITIONAL, level="senior")
        external_reviewer = Reviewer(id="2", display_name="External", tier=ReviewTier.ADDITIONAL, level=None)

        # when
        ordered = sorted([external_reviewer, known_reviewer], key=reviewer_seniority().approval_sort_key)

        # then
        self.assertEqual([known_reviewer, external_reviewer], ordered)


if __name__ == '__main__':
    unittest.main()
