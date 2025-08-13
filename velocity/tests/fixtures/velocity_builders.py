from datetime import datetime, timedelta
from typing import Optional, Dict

from sd_metrics_lib.utils.time import Duration, TimeUnit

from velocity.app.domain.model.task import Task, Assignee, Assignment, TimeTracking
from velocity.app.domain.model.velocity import ReportGenerationParameters, ReportType, VelocityReport
from velocity.app.domain.model.config import MemberVelocityConfig, CalculationConfig, WorkflowConfig


class TaskBuilder:
    def __init__(self):
        self._id = "TASK-123"
        self._title = "Sample Task"
        self._completed_at = datetime.now() - timedelta(days=1)
        self._story_points = None
        self._assignment = None
        self._time_tracking = None

    @classmethod
    def sprint_task(cls):
        return cls().with_id("SPRINT-101").with_title("Sprint Planning Feature")

    @classmethod
    def retrospective_task(cls):
        return cls().with_id("RETRO-201").with_title("Team Retrospective Improvements")

    @classmethod
    def capacity_planning_task(cls):
        return cls().with_id("CAP-301").with_title("Capacity Planning Tool")

    def with_id(self, task_id: str):
        self._id = task_id
        return self

    def with_title(self, title: str):
        self._title = title
        return self

    def completed_yesterday(self):
        self._completed_at = datetime.now() - timedelta(days=1)
        return self

    def completed_last_week(self):
        self._completed_at = datetime.now() - timedelta(days=7)
        return self

    def completed_on(self, completion_date: datetime):
        self._completed_at = completion_date
        return self

    def with_story_points(self, points: float):
        self._story_points = points
        return self

    def assigned_to_senior_developer(self):
        assignee = Assignee(id="senior-dev", display_name="Senior Developer")
        self._assignment = Assignment(assignee=assignee)
        return self

    def assigned_to_junior_developer(self):
        assignee = Assignee(id="junior-dev", display_name="Junior Developer")
        self._assignment = Assignment(assignee=assignee)
        return self

    def assigned_to(self, member_id: str, display_name: str):
        assignee = Assignee(id=member_id, display_name=display_name)
        self._assignment = Assignment(assignee=assignee)
        return self

    def with_time_spent(self, hours: float):
        total_time = Duration.of(hours, TimeUnit.HOUR)
        assignee_time = {}
        if self._assignment and self._assignment.assignee:
            assignee_time[self._assignment.assignee.id] = total_time
        
        self._time_tracking = TimeTracking(
            total_spent_time=total_time,
            spent_time_by_assignee=assignee_time
        )
        return self

    def with_distributed_time_spent(self, time_by_assignee: Dict[str, float]):
        total_hours = sum(time_by_assignee.values())
        total_time = Duration.of(total_hours, TimeUnit.HOUR)
        assignee_times = {
            assignee_id: Duration.of(hours, TimeUnit.HOUR) 
            for assignee_id, hours in time_by_assignee.items()
        }
        
        self._time_tracking = TimeTracking(
            total_spent_time=total_time,
            spent_time_by_assignee=assignee_times
        )
        return self

    def with_no_time_tracking(self):
        self._time_tracking = None
        return self

    def build(self) -> Task:
        return Task(
            id=self._id,
            title=self._title,
            completed_at=self._completed_at,
            story_points=self._story_points,
            assignment=self._assignment,
            time_tracking=self._time_tracking
        )


class ReportParametersBuilder:
    def __init__(self):
        self._time_unit = TimeUnit.MONTH
        self._number_of_periods = 3
        self._report_type = None
        self._scope_id = None

    @classmethod
    def sprint_planning_report(cls):
        return cls().for_member_group_scope().over_last_months(6)

    @classmethod
    def retrospective_analysis(cls):
        return cls().for_member_scope().over_last_weeks(4)

    @classmethod
    def capacity_planning_report(cls):
        return cls().for_member_group_scope().over_last_quarters(2)

    def for_member_group_scope(self):
        self._report_type = ReportType.MEMBER_GROUP_SCOPE
        return self

    def for_member_scope(self):
        self._report_type = ReportType.MEMBER_SCOPE
        return self

    def over_last_months(self, count: int):
        self._time_unit = TimeUnit.MONTH
        self._number_of_periods = count
        return self

    def over_last_weeks(self, count: int):
        self._time_unit = TimeUnit.WEEK
        self._number_of_periods = count
        return self

    def over_last_quarters(self, count: int):
        self._time_unit = TimeUnit.MONTH
        self._number_of_periods = count * 3
        return self

    def for_scope(self, scope_id: str):
        self._scope_id = scope_id
        return self

    def build(self) -> ReportGenerationParameters:
        return ReportGenerationParameters(
            time_unit=self._time_unit,
            number_of_periods=self._number_of_periods,
            report_type=self._report_type,
            scope_id=self._scope_id
        )


class VelocityConfigBuilder:
    def __init__(self):
        self._calculation = CalculationConfig(
            working_days_per_month=20,
            default_story_points_value_when_missing=1.0
        )
        self._workflow = WorkflowConfig(
            done_status_codes=["Done", "Closed", "Resolved"]
        )
        self._member_velocity = MemberVelocityConfig(
            story_points_to_ideal_hours_ratio=4.0,
            seniority_levels={"senior": 1.0, "junior": 2.0},
            members={},
            default_seniority_level="junior"
        )

    @classmethod
    def sprint_planning_team(cls):
        return (cls()
                .with_senior_members(["alice", "bob"])
                .with_junior_members(["carol", "dave"])
                .with_story_points_ratio(6.0))

    @classmethod
    def retrospective_team(cls):
        return (cls()
                .with_senior_members(["eve", "frank"])
                .with_junior_members(["grace"])
                .with_story_points_ratio(4.0))

    def with_senior_members(self, member_ids: list):
        for member_id in member_ids:
            self._member_velocity.members[member_id] = {
                "level": "senior",
                "member_groups": ["development-team"]
            }
        return self

    def with_junior_members(self, member_ids: list):
        for member_id in member_ids:
            self._member_velocity.members[member_id] = {
                "level": "junior", 
                "member_groups": ["development-team"]
            }
        return self

    def with_story_points_ratio(self, ratio: float):
        self._member_velocity.story_points_to_ideal_hours_ratio = ratio
        return self

    def with_working_days_per_month(self, days: int):
        self._calculation.working_days_per_month = days
        return self

    def build(self) -> MemberVelocityConfig:
        return self._member_velocity


class BusinessScenarios:
    
    @staticmethod
    def sprint_planning_tasks():
        return [
            TaskBuilder.sprint_task()
                .with_story_points(8.0)
                .assigned_to_senior_developer()
                .with_time_spent(12.0)
                .completed_yesterday()
                .build(),
            TaskBuilder.capacity_planning_task()
                .with_story_points(5.0)
                .assigned_to_junior_developer()
                .with_time_spent(20.0)
                .completed_last_week()
                .build()
        ]

    @staticmethod
    def retrospective_analysis_tasks():
        return [
            TaskBuilder.retrospective_task()
                .with_story_points(3.0)
                .assigned_to("team-lead", "Team Lead")
                .with_time_spent(4.5)
                .completed_yesterday()
                .build()
        ]

    @staticmethod
    def high_performing_team_tasks():
        return [
            TaskBuilder.sprint_task()
                .with_story_points(13.0)
                .assigned_to_senior_developer()
                .with_time_spent(10.0)
                .completed_yesterday()
                .build(),
            TaskBuilder.capacity_planning_task()
                .with_story_points(8.0)
                .assigned_to_junior_developer()
                .with_time_spent(8.0)
                .completed_yesterday()
                .build()
        ]

    @staticmethod
    def underperforming_team_tasks():
        return [
            TaskBuilder.sprint_task()
                .with_story_points(2.0)
                .assigned_to_senior_developer()
                .with_time_spent(20.0)
                .completed_yesterday()
                .build()
        ]