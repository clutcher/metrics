import unittest
from types import SimpleNamespace

from pull_requests.out.convertors.azure_review import AzureReviewConverter

_REVIEWERS_TYPE_ID = "fd2167ab-b0be-447a-8ec8-39368250530e"


_BUILD_TYPE_ID = "0609b952-1397-4640-95ec-e00a01b2c241"


def policy_record(status: str, is_blocking: bool = True, is_enabled: bool = True,
                  is_deleted: bool = False, name: str = "Required reviewers",
                  type_id: str = _REVIEWERS_TYPE_ID, context=None):
    return SimpleNamespace(
        status=status,
        context=context,
        configuration=SimpleNamespace(
            id=1,
            is_blocking=is_blocking,
            is_enabled=is_enabled,
            is_deleted=is_deleted,
            type=SimpleNamespace(id=type_id, display_name=name)
        )
    )


class TestAzureReviewConverterPolicyFiltering(unittest.TestCase):

    def test_shouldKeepEvaluationWhenPolicyIsBlocking(self):
        # given
        records = [policy_record("approved", is_blocking=True)]

        # when
        review_inputs = AzureReviewConverter().to_review_inputs(None, None, records)

        # then
        self.assertEqual(1, len(review_inputs.policy_evaluations))

    def test_shouldDropEvaluationWhenPolicyIsOptional(self):
        # given
        records = [policy_record("queued", is_blocking=False)]

        # when
        review_inputs = AzureReviewConverter().to_review_inputs(None, None, records)

        # then
        self.assertEqual([], review_inputs.policy_evaluations)

    def test_shouldDropEvaluationWhenPolicyIsDeleted(self):
        # given
        records = [policy_record("approved", is_deleted=True)]

        # when
        review_inputs = AzureReviewConverter().to_review_inputs(None, None, records)

        # then
        self.assertEqual([], review_inputs.policy_evaluations)

    def test_shouldDropEvaluationWhenPolicyIsDisabled(self):
        # given
        records = [policy_record("approved", is_enabled=False)]

        # when
        review_inputs = AzureReviewConverter().to_review_inputs(None, None, records)

        # then
        self.assertEqual([], review_inputs.policy_evaluations)

    def test_shouldParseExpiredFlagWhenBuildContextMarksItExpired(self):
        # given
        records = [policy_record("queued", name="Build", type_id=_BUILD_TYPE_ID, context={"isExpired": True})]

        # when
        review_inputs = AzureReviewConverter().to_review_inputs(None, None, records)

        # then
        self.assertTrue(review_inputs.policy_evaluations[0].is_expired)


class TestAzureReviewConverterMergeConflict(unittest.TestCase):

    def test_shouldFlagMergeConflictWhenBranchHasConflicts(self):
        # given
        merge_status = "conflicts"

        # when
        review_inputs = AzureReviewConverter().to_review_inputs(None, None, None, merge_status)

        # then
        self.assertTrue(review_inputs.has_merge_conflict)

    def test_shouldNotFlagMergeConflictWhenBranchMergesCleanly(self):
        # given
        merge_status = "succeeded"

        # when
        review_inputs = AzureReviewConverter().to_review_inputs(None, None, None, merge_status)

        # then
        self.assertFalse(review_inputs.has_merge_conflict)

    def test_shouldNotFlagMergeConflictWhenMergeStatusUnknown(self):
        # given
        # when
        review_inputs = AzureReviewConverter().to_review_inputs(None, None, None)

        # then
        self.assertFalse(review_inputs.has_merge_conflict)


if __name__ == '__main__':
    unittest.main()
