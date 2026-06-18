import unittest
from datetime import datetime, timezone

from pull_requests.app.domain.model.pull_request import ApprovalVote
from pull_requests.app.domain.model.review import PolicyCategory, PolicyEvaluationStatus
from pull_requests.out.convertors.bitbucket_review import BitbucketReviewConverter


def reviewer(account_id: str, display_name: str):
    return {'account_id': account_id, 'display_name': display_name}


def participant(account_id: str, display_name: str, state, approved: bool, role: str = 'REVIEWER'):
    return {'role': role, 'approved': approved, 'state': state, 'user': reviewer(account_id, display_name)}


def approval_event(account_id: str, display_name: str, date: str):
    return {'approval': {'date': date, 'user': reviewer(account_id, display_name)}}


def changes_requested_event(account_id: str, display_name: str, date: str):
    return {'changes_requested': {'date': date, 'user': reviewer(account_id, display_name)}}


def update_event(date: str):
    return {'update': {'date': date, 'source': {'commit': {'hash': 'abc123'}}}}


def build_status(state: str, key: str = 'pipeline', name: str = 'Pipeline'):
    return {'type': 'build', 'key': key, 'name': name, 'state': state}


class TestBitbucketReviewConverterVoteEvents(unittest.TestCase):

    def test_shouldRecordPositiveVoteEventWhenReviewerApproved(self):
        # given
        activity = [approval_event('acc-anna', 'Anna Dev', '2026-06-01T10:00:00+00:00')]

        # when
        review_inputs = BitbucketReviewConverter().to_review_inputs(None, activity, None)

        # then
        vote_event = review_inputs.vote_events[0]
        self.assertEqual(
            (ApprovalVote.APPROVED, datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc), 'acc-anna'),
            (vote_event.vote, vote_event.occurred_at, vote_event.reviewer_id)
        )

    def test_shouldRecordRejectionVoteEventWhenReviewerRequestedChanges(self):
        # given
        activity = [changes_requested_event('acc-bob', 'Bob Lead', '2026-06-02T09:30:00+00:00')]

        # when
        review_inputs = BitbucketReviewConverter().to_review_inputs(None, activity, None)

        # then
        self.assertEqual(ApprovalVote.REJECTED, review_inputs.vote_events[0].vote)

    def test_shouldIgnoreCommitUpdateActivityWhenBuildingVoteEvents(self):
        # given
        activity = [update_event('2026-06-03T08:00:00+00:00')]

        # when
        review_inputs = BitbucketReviewConverter().to_review_inputs(None, activity, None)

        # then
        self.assertEqual([], review_inputs.vote_events)


class TestBitbucketReviewConverterCurrentApprovals(unittest.TestCase):

    def test_shouldReflectActiveApprovalWhenParticipantStillApproves(self):
        # given
        participants = [participant('acc-anna', 'Anna Dev', state='approved', approved=True)]

        # when
        review_inputs = BitbucketReviewConverter().to_review_inputs(participants, None, None)

        # then
        self.assertEqual(ApprovalVote.APPROVED, review_inputs.current_approvals[0].vote)

    def test_shouldClearApprovalWhenNewCommitResetParticipantVote(self):
        # given
        participants = [participant('acc-anna', 'Anna Dev', state=None, approved=False)]

        # when
        review_inputs = BitbucketReviewConverter().to_review_inputs(participants, None, None)

        # then
        self.assertEqual(ApprovalVote.NO_VOTE, review_inputs.current_approvals[0].vote)


class TestBitbucketReviewConverterBuildPolicies(unittest.TestCase):

    def test_shouldApproveBuildPolicyWhenPipelineSucceeded(self):
        # given
        statuses = [build_status('SUCCESSFUL')]

        # when
        review_inputs = BitbucketReviewConverter().to_review_inputs(None, None, statuses)

        # then
        evaluation = review_inputs.policy_evaluations[0]
        self.assertEqual(
            (PolicyCategory.BUILD, PolicyEvaluationStatus.APPROVED),
            (evaluation.category, evaluation.status)
        )

    def test_shouldRejectBuildPolicyWhenPipelineFailed(self):
        # given
        statuses = [build_status('FAILED')]

        # when
        review_inputs = BitbucketReviewConverter().to_review_inputs(None, None, statuses)

        # then
        self.assertEqual(PolicyEvaluationStatus.REJECTED, review_inputs.policy_evaluations[0].status)

    def test_shouldMarkBuildPolicyRunningWhenPipelineInProgress(self):
        # given
        statuses = [build_status('INPROGRESS')]

        # when
        review_inputs = BitbucketReviewConverter().to_review_inputs(None, None, statuses)

        # then
        self.assertEqual(PolicyEvaluationStatus.RUNNING, review_inputs.policy_evaluations[0].status)


if __name__ == '__main__':
    unittest.main()
