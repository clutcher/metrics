from typing import Dict, List

from ..data.pull_request_data import PersonActivitySummaryData, PullRequestData


class PullRequestSummaryUtils:

    @staticmethod
    def build_person_activity(pull_requests: List[PullRequestData]) -> List[PersonActivitySummaryData]:
        activity_by_person: Dict[str, PersonActivitySummaryData] = {}

        def activity_for(display_name: str) -> PersonActivitySummaryData:
            activity = activity_by_person.get(display_name)
            if activity is None:
                activity = PersonActivitySummaryData(display_name=display_name)
                activity_by_person[display_name] = activity
            return activity

        for pull_request in pull_requests:
            activity_for(pull_request.author_name).created_count += 1
            for approval in pull_request.approvals:
                reviewer_activity = activity_for(approval.display_name)
                if approval.is_approval:
                    reviewer_activity.approved_count += 1
                else:
                    reviewer_activity.changes_requested_count += 1

        return sorted(
            activity_by_person.values(),
            key=lambda activity: (-activity.approved_count, -activity.created_count, activity.display_name.lower())
        )
