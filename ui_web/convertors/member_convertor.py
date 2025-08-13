from typing import List

from sd_metrics_lib.utils.time import TimeUnit, TimePolicy

from tasks.app.domain.model.task import MemberGroup
from ..data.member_data import MemberData, MemberGroupData


class MemberConvertor:

    def convert_members_with_workload_to_data(self, member_ids: List[str], all_historical_tasks: List) -> List[
        MemberData]:
        if not member_ids:
            return []

        member_tasks_map = self._group_tasks_by_member(all_historical_tasks, member_ids)

        members = []
        for member_id in member_ids:
            member_tasks = member_tasks_map.get(member_id, [])
            total_hours = self._calculate_total_hours_workload(member_id, member_tasks)
            ticket_count = len(member_tasks)
            hours_per_task = total_hours / ticket_count if ticket_count > 0 else 0.0

            member = MemberData(
                member_id=member_id,
                display_name=member_id,
                total_hours_last_30=total_hours,
                tickets_assigned_last_30=ticket_count,
                hours_per_task=hours_per_task,
                total_work_days_last_30=TimePolicy.BUSINESS_HOURS.convert(total_hours, TimeUnit.HOUR, TimeUnit.DAY)
            )
            members.append(member)

        members.sort(key=lambda m: -m.total_hours_last_30)
        return members

    @staticmethod
    def convert_member_group_to_data(member_group: MemberGroup) -> MemberGroupData:
        return MemberGroupData(
            id=member_group.id,
            name=member_group.name
        )

    @staticmethod
    def _group_tasks_by_member(tasks: List, available_member_ids: List[str]) -> dict:
        member_tasks_map = {member_id: [] for member_id in available_member_ids}

        for task in tasks:
            if (task.time_tracking and
                    task.time_tracking.spent_time_by_assignee):
                for member_id in task.time_tracking.spent_time_by_assignee:
                    if member_id in available_member_ids:
                        member_tasks_map[member_id].append(task)

        return member_tasks_map

    @staticmethod
    def _calculate_total_hours_workload(member_id: str, historical_tasks: List) -> float:
        total_hours = 0.0

        for task in historical_tasks:
            if (task.time_tracking and
                    task.time_tracking.spent_time_by_assignee and
                    member_id in task.time_tracking.spent_time_by_assignee):
                time_duration = task.time_tracking.spent_time_by_assignee[member_id]
                hours = time_duration.convert(TimeUnit.HOUR).time_delta
                total_hours += hours

        return total_hours
