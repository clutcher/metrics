from datetime import datetime
from typing import List, Optional

from sd_metrics_lib.utils.enums import HealthStatus
from sd_metrics_lib.utils.time import Duration, TimeUnit

from tasks.app.domain.model.task import Task, Assignment, Assignee, TimeTracking, SystemMetadata, TaskStatus, MemberGroup
from ui_web.data.task_data import TaskData, AssignmentData, AssigneeData, TimeTrackingData, SystemMetadataData, ForecastData
from ui_web.data.member_data import MemberGroupData
from ui_web.data.hierarchical_item_data import HierarchicalItemData


class TaskDataBuilder:
    
    def __init__(self, task_id: str, title: str):
        self._id = task_id
        self._title = title
        self._story_points: Optional[float] = None
        self._priority: Optional[int] = None
        self._assignee_data: Optional[AssigneeData] = None
        self._member_group_data: Optional[MemberGroupData] = None
        self._total_spent_time_days: Optional[float] = None
        self._current_assignee_spent_time_days: Optional[float] = None
        self._stage: Optional[str] = None
        self._original_status = "To Do"
        self._url: Optional[str] = None
        self._child_tasks: List[TaskData] = []
        self._child_tasks_count = 0
        self._forecast_data: Optional[ForecastData] = None
    
    @classmethod
    def sprint_dashboard_task(cls) -> 'TaskDataBuilder':
        return cls("PROJ-123", "Implement user authentication dashboard")
    
    @classmethod
    def team_velocity_task(cls) -> 'TaskDataBuilder':
        return cls("PROJ-456", "Optimize database queries for reporting")
    
    @classmethod
    def capacity_planning_epic(cls) -> 'TaskDataBuilder':
        return cls("PROJ-001", "Customer Management Epic")
    
    @classmethod
    def retrospective_analysis_task(cls) -> 'TaskDataBuilder':
        return cls("PROJ-789", "Refactor legacy authentication system")
    
    @classmethod
    def health_monitoring_task(cls) -> 'TaskDataBuilder':
        return cls("PROJ-321", "Set up application monitoring")
    
    def with_story_points(self, points: float) -> 'TaskDataBuilder':
        self._story_points = points
        return self

    def with_priority(self, priority: int) -> 'TaskDataBuilder':
        self._priority = priority
        return self

    def assigned_to(self, assignee_id: str) -> 'TaskDataBuilder':
        self._assignee_data = AssigneeData(
            id=assignee_id,
            display_name=f"{assignee_id} (Developer)",
            avatar_url=f"https://company.com/avatars/{assignee_id}.jpg"
        )
        return self
    
    def assigned_to_frontend_team_senior(self) -> 'TaskDataBuilder':
        self._assignee_data = AssigneeData(
            id="alice.frontend",
            display_name="Alice Johnson (Senior Frontend Developer)",
            avatar_url="https://company.com/avatars/alice.jpg"
        )
        self._member_group_data = MemberGroupData(
            id="frontend-team",
            name="Frontend Development Team"
        )
        return self
    
    def assigned_to_backend_team_junior(self) -> 'TaskDataBuilder':
        self._assignee_data = AssigneeData(
            id="bob.backend",
            display_name="Bob Smith (Junior Backend Developer)",
            avatar_url="https://company.com/avatars/bob.jpg"
        )
        self._member_group_data = MemberGroupData(
            id="backend-team",
            name="Backend Development Team"
        )
        return self
    
    def assigned_to_devops_team_lead(self) -> 'TaskDataBuilder':
        self._assignee_data = AssigneeData(
            id="charlie.devops",
            display_name="Charlie Wilson (DevOps Team Lead)",
            avatar_url="https://company.com/avatars/charlie.jpg"
        )
        self._member_group_data = MemberGroupData(
            id="devops-team",
            name="DevOps Team"
        )
        return self
    
    def with_no_assignee(self) -> 'TaskDataBuilder':
        self._assignee_data = None
        self._member_group_data = None
        return self
    
    def with_time_spent_days(self, days: float) -> 'TaskDataBuilder':
        self._total_spent_time_days = days
        self._current_assignee_spent_time_days = days
        return self
    
    def with_stage(self, stage: str) -> 'TaskDataBuilder':
        self._stage = stage
        return self
    
    def in_development_stage(self) -> 'TaskDataBuilder':
        return self.with_stage("development")
    
    def in_qa_stage(self) -> 'TaskDataBuilder':
        return self.with_stage("qa")
    
    def in_done_stage(self) -> 'TaskDataBuilder':
        return self.with_stage("done")
    
    def with_green_health_forecast(self) -> 'TaskDataBuilder':
        self._forecast_data = ForecastData(
            health_status=HealthStatus.GREEN,
            estimation_time_days=2.5,
            start_date=datetime.now().isoformat(),
            velocity=8.5
        )
        return self
    
    def with_yellow_health_forecast(self) -> 'TaskDataBuilder':
        self._forecast_data = ForecastData(
            health_status=HealthStatus.YELLOW,
            estimation_time_days=5.0,
            start_date=datetime.now().isoformat(),
            velocity=6.2
        )
        return self
    
    def with_red_health_forecast(self) -> 'TaskDataBuilder':
        self._forecast_data = ForecastData(
            health_status=HealthStatus.RED,
            estimation_time_days=10.0,
            start_date=datetime.now().isoformat(),
            velocity=3.1
        )
        return self
    
    def with_child_tasks(self, *child_tasks: TaskData) -> 'TaskDataBuilder':
        self._child_tasks = list(child_tasks)
        self._child_tasks_count = len(child_tasks)
        return self
    
    def with_original_status(self, status: str) -> 'TaskDataBuilder':
        self._original_status = status
        return self
    
    def with_url(self, url: str) -> 'TaskDataBuilder':
        self._url = url
        return self
    
    def build(self) -> TaskData:
        assignment = AssignmentData(
            assignee=self._assignee_data,
            member_group=self._member_group_data
        )
        
        time_tracking = TimeTrackingData(
            total_spent_time_days=self._total_spent_time_days,
            current_assignee_spent_time_days=self._current_assignee_spent_time_days
        )
        
        system_metadata = SystemMetadataData(
            original_status=self._original_status,
            url=self._url
        )
        
        return TaskData(
            id=self._id,
            title=self._title,
            assignment=assignment,
            time_tracking=time_tracking,
            system_metadata=system_metadata,
            story_points=self._story_points,
            priority=self._priority,
            child_tasks=self._child_tasks if self._child_tasks else None,
            child_tasks_count=self._child_tasks_count,
            stage=self._stage,
            forecast=self._forecast_data
        )


class DomainTaskBuilder:
    
    def __init__(self, task_id: str, title: str):
        self._id = task_id
        self._title = title
        self._created_at = datetime(2024, 1, 1, 10, 0, 0)
        self._updated_at = datetime(2024, 1, 15, 14, 30, 0)
        self._story_points: Optional[float] = None
        self._assignee: Optional[Assignee] = None
        self._member_group: Optional[MemberGroup] = None
        self._total_spent_time: Optional[Duration] = None
        self._child_tasks: List[Task] = []
        self._status: Optional[TaskStatus] = None
        self._stage: Optional[str] = None
        self._original_status = "To Do"
        self._project_key = "PROJ"
        self._url: Optional[str] = None
    
    @classmethod
    def domain_task_for_ui_conversion(cls) -> 'DomainTaskBuilder':
        return (cls("PROJ-123", "Domain task for UI conversion testing")
                .assigned_to("default.developer"))
    
    def with_story_points(self, points: float) -> 'DomainTaskBuilder':
        self._story_points = points
        return self
    
    def assigned_to(self, assignee_id: str) -> 'DomainTaskBuilder':
        self._assignee = Assignee(
            id=assignee_id,
            display_name=f"{assignee_id} (Developer)",
            avatar_url=f"https://company.com/avatars/{assignee_id.replace('.', '_')}.jpg"
        )
        return self
    
    def assigned_to_senior_developer(self) -> 'DomainTaskBuilder':
        self._assignee = Assignee(
            id="alice.senior",
            display_name="Alice Thompson (Senior Developer)",
            avatar_url="https://company.com/avatars/alice.jpg"
        )
        self._member_group = MemberGroup(id="backend-team", name="Backend Team")
        return self
    
    def with_time_spent_hours(self, hours: float) -> 'DomainTaskBuilder':
        self._total_spent_time = Duration.of(hours, TimeUnit.HOUR)
        return self
    
    def with_stage(self, stage: str) -> 'DomainTaskBuilder':
        self._stage = stage
        return self
    
    def build(self) -> Task:
        assignment = Assignment(
            assignee=self._assignee,
            member_group=self._member_group
        )
        
        time_tracking = TimeTracking(
            total_spent_time=self._total_spent_time
        )
        
        system_metadata = SystemMetadata(
            original_status=self._original_status,
            project_key=self._project_key,
            url=self._url
        )
        
        return Task(
            id=self._id,
            title=self._title,
            created_at=self._created_at,
            updated_at=self._updated_at,
            system_metadata=system_metadata,
            assignment=assignment,
            time_tracking=time_tracking,
            status=self._status,
            stage=self._stage,
            story_points=self._story_points,
            child_tasks=self._child_tasks if self._child_tasks else None
        )


class BusinessScenarios:
    """
    Business-focused test scenarios that represent real stakeholder concerns.
    
    Each scenario provides:
    - Realistic business context for stakeholders (PMs, Scrum Masters, Developers)
    - Test data that reflects actual work patterns and team dynamics
    - Scenarios that inform business decisions about capacity, performance, and health
    """
    
    @staticmethod
    def critical_production_incident_response() -> List[TaskData]:
        """
        Scenario: Critical production bug requiring immediate team response
        
        Business Context: High-priority incident affecting customer experience
        Stakeholder Value: Helps identify response time and resource allocation for incidents
        Decision Impact: Informs escalation policies and incident response team capacity
        """
        return [
            TaskDataBuilder.sprint_dashboard_task()
                .with_story_points(8.0)
                .assigned_to_backend_team_junior()
                .with_time_spent_days(2.0)
                .in_development_stage()
                .with_red_health_forecast()
                .with_original_status("In Progress")
                .build(),
            
            TaskDataBuilder.health_monitoring_task()
                .with_story_points(5.0)
                .assigned_to_devops_team_lead()
                .with_time_spent_days(1.5)
                .in_qa_stage()
                .with_yellow_health_forecast()
                .with_original_status("Testing")
                .build()
        ]
    
    @staticmethod
    def successful_sprint_completion() -> List[TaskData]:
        """
        Scenario: Successful sprint with all tasks completed on schedule
        
        Business Context: Team delivering on commitments for stakeholder confidence
        Stakeholder Value: Demonstrates team reliability and predictable delivery capacity
        Decision Impact: Supports sprint planning accuracy and velocity forecasting
        """
        return [
            TaskDataBuilder.sprint_dashboard_task()
                .with_story_points(5.0)
                .assigned_to_frontend_team_senior()
                .with_time_spent_days(2.0)
                .in_done_stage()
                .with_green_health_forecast()
                .with_original_status("Done")
                .build(),
            
            TaskDataBuilder.team_velocity_task()
                .with_story_points(3.0)
                .assigned_to_backend_team_junior()
                .with_time_spent_days(1.5)
                .in_done_stage()
                .with_green_health_forecast()
                .with_original_status("Done")
                .build()
        ]
    
    @staticmethod
    def capacity_planning_scenario() -> List[TaskData]:
        """
        Scenario: Mixed workload requiring capacity planning decisions
        Business Context: Product manager needs to allocate resources effectively
        """
        return [
            TaskDataBuilder.capacity_planning_epic()
                .with_story_points(13.0)
                .assigned_to_frontend_team_senior()
                .with_time_spent_days(8.0)
                .in_development_stage()
                .with_yellow_health_forecast()
                .build(),
            
            TaskDataBuilder.retrospective_analysis_task()
                .with_story_points(2.0)
                .assigned_to_backend_team_junior()
                .with_time_spent_days(1.0)
                .in_qa_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder.health_monitoring_task()
                .with_story_points(5.0)
                .with_no_assignee()  # Unassigned - needs capacity allocation
                .with_time_spent_days(0.0)
                .with_stage("backlog")
                .with_original_status("To Do")
                .build()
        ]
    
    @staticmethod
    def one_on_one_performance_review() -> List[TaskData]:
        """
        Scenario: Individual developer performance data for one-on-one reviews
        Business Context: Manager preparing for performance discussions
        """
        return [
            TaskDataBuilder.sprint_dashboard_task()
                .with_story_points(8.0)
                .assigned_to("alice.senior.developer")
                .with_time_spent_days(3.0)  # Efficient completion
                .in_done_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder.team_velocity_task()
                .with_story_points(5.0)
                .assigned_to("alice.senior.developer")
                .with_time_spent_days(2.5)  # Good velocity
                .in_done_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder.retrospective_analysis_task()
                .with_story_points(3.0)
                .assigned_to("alice.senior.developer")
                .with_time_spent_days(1.5)  # Consistent performance
                .in_done_stage()
                .with_green_health_forecast()
                .build()
        ]
    
    @staticmethod
    def technical_debt_prioritization() -> List[TaskData]:
        """
        Scenario: Technical debt tasks competing with feature development
        Business Context: Engineering manager balancing debt vs features
        """
        return [
            TaskDataBuilder.retrospective_analysis_task()
                .with_story_points(8.0)
                .assigned_to_backend_team_junior()
                .with_time_spent_days(5.0)  # High effort, important refactoring
                .in_development_stage()
                .with_yellow_health_forecast()
                .with_original_status("In Progress")
                .build(),
            
            TaskDataBuilder("TECH-DEBT-001", "Upgrade legacy authentication system")
                .with_story_points(13.0)
                .assigned_to_devops_team_lead()
                .with_time_spent_days(10.0)  # Significant technical debt
                .in_qa_stage()
                .with_red_health_forecast()
                .with_original_status("Testing")
                .build()
        ]
    
    @staticmethod
    def cross_team_collaboration_epic() -> List[TaskData]:
        """
        Scenario: Epic requiring coordination across multiple teams
        Business Context: Product owner tracking cross-functional delivery
        """
        return [
            TaskDataBuilder("EPIC-COLLAB-001", "Multi-tenant Architecture Implementation")
                .with_story_points(21.0)
                .assigned_to_backend_team_junior()
                .with_time_spent_days(12.0)
                .in_development_stage()
                .with_yellow_health_forecast()
                .build(),
            
            TaskDataBuilder("EPIC-COLLAB-002", "Frontend Multi-tenant UI Components")
                .with_story_points(13.0)
                .assigned_to_frontend_team_senior()
                .with_time_spent_days(8.0)
                .in_development_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder("EPIC-COLLAB-003", "DevOps Multi-tenant Deployment Pipeline")
                .with_story_points(8.0)
                .assigned_to_devops_team_lead()
                .with_time_spent_days(4.0)
                .in_qa_stage()
                .with_green_health_forecast()
                .build()
        ]
    
    @staticmethod
    def new_team_member_onboarding() -> List[TaskData]:
        """
        Scenario: Onboarding tasks for new team member evaluation
        Business Context: Team lead assessing onboarding progress and support needs
        """
        return [
            TaskDataBuilder("ONBOARD-001", "Set up development environment")
                .with_story_points(2.0)
                .assigned_to("junior.new.developer")
                .with_time_spent_days(1.0)
                .in_done_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder("ONBOARD-002", "First code contribution - bug fix")
                .with_story_points(3.0)
                .assigned_to("junior.new.developer")
                .with_time_spent_days(2.5)  # Slower pace expected
                .in_qa_stage()
                .with_yellow_health_forecast()
                .build(),
            
            TaskDataBuilder("ONBOARD-003", "Code review learning task")
                .with_story_points(1.0)
                .assigned_to("junior.new.developer")
                .with_time_spent_days(0.5)
                .in_development_stage()
                .with_green_health_forecast()
                .build()
        ]
    
    @staticmethod
    def sprint_dashboard_tasks() -> List[TaskData]:
        return [
            TaskDataBuilder.sprint_dashboard_task()
                .with_story_points(5.0)
                .assigned_to_frontend_team_senior()
                .with_time_spent_days(1.5)
                .in_development_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder.team_velocity_task()
                .with_story_points(8.0)
                .assigned_to_backend_team_junior()
                .with_time_spent_days(3.0)
                .in_qa_stage()
                .with_yellow_health_forecast()
                .build(),
            
            TaskDataBuilder.health_monitoring_task()
                .with_story_points(3.0)
                .assigned_to_devops_team_lead()
                .with_time_spent_days(0.5)
                .in_development_stage()
                .with_green_health_forecast()
                .build()
        ]
    
    @staticmethod
    def team_capacity_analysis_tasks() -> List[TaskData]:
        return [
            TaskDataBuilder.capacity_planning_epic()
                .with_story_points(10.0)
                .assigned_to_frontend_team_senior()
                .with_time_spent_days(5.0)
                .in_done_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder.retrospective_analysis_task()
                .with_story_points(2.0)
                .assigned_to_backend_team_junior()
                .with_time_spent_days(4.0)
                .in_qa_stage()
                .with_red_health_forecast()
                .build()
        ]
    
    @staticmethod
    def mixed_member_group_tasks() -> List[TaskData]:
        return [
            TaskDataBuilder.sprint_dashboard_task()
                .assigned_to_frontend_team_senior()
                .in_development_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder.team_velocity_task()
                .assigned_to_backend_team_junior()
                .in_qa_stage()
                .with_yellow_health_forecast()
                .build(),
            
            TaskDataBuilder.health_monitoring_task()
                .assigned_to_devops_team_lead()
                .in_development_stage()
                .with_green_health_forecast()
                .build()
        ]
    
    @staticmethod
    def mixed_stage_tasks() -> List[TaskData]:
        return [
            TaskDataBuilder.sprint_dashboard_task()
                .assigned_to_frontend_team_senior()
                .in_development_stage()
                .with_green_health_forecast()
                .build(),
            
            TaskDataBuilder.team_velocity_task()
                .assigned_to_frontend_team_senior()
                .in_qa_stage()
                .with_yellow_health_forecast()
                .build(),
            
            TaskDataBuilder.health_monitoring_task()
                .assigned_to_frontend_team_senior()
                .in_done_stage()
                .with_green_health_forecast()
                .build()
        ]
    
    @staticmethod
    def tasks_for_sorting_by_spent_time() -> List[TaskData]:
        return [
            TaskDataBuilder.sprint_dashboard_task().with_time_spent_days(1.0).build(),
            TaskDataBuilder.team_velocity_task().with_time_spent_days(5.0).build(),
            TaskDataBuilder.health_monitoring_task().with_time_spent_days(3.0).build()
        ]
    
    @staticmethod
    def unassigned_tasks() -> List[TaskData]:
        return [
            TaskDataBuilder.sprint_dashboard_task().with_no_assignee().build(),
            TaskDataBuilder.team_velocity_task().with_no_assignee().build()
        ]
    
    @staticmethod
    def hierarchical_epic_with_children() -> TaskData:
        child1 = (TaskDataBuilder("PROJ-002", "Epic Child 1")
                  .with_story_points(3.0)
                  .assigned_to_frontend_team_senior()
                  .in_development_stage()
                  .build())
        
        child2 = (TaskDataBuilder("PROJ-003", "Epic Child 2")
                  .with_story_points(5.0)
                  .assigned_to_backend_team_junior()
                  .in_qa_stage()
                  .build())
        
        return (TaskDataBuilder.capacity_planning_epic()
                .with_story_points(10.0)
                .assigned_to_devops_team_lead()
                .with_child_tasks(child1, child2)
                .in_development_stage()
                .build())
    
    @staticmethod
    def active_sprint_tasks() -> List[Task]:
        return [
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .with_story_points(5.0)
                .assigned_to("alice.johnson")
                .with_time_spent_hours(16.0)
                .with_stage("development")
                .build(),
            
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .with_story_points(8.0)
                .assigned_to("bob.smith")
                .with_time_spent_hours(12.0)
                .with_stage("qa")
                .build(),
            
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .with_story_points(3.0)
                .assigned_to("charlie.brown")
                .with_time_spent_hours(8.0)
                .with_stage("development")
                .build()
        ]
    
    @staticmethod
    def recently_completed_tasks() -> List[Task]:
        return [
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .with_story_points(3.0)
                .assigned_to("charlie.brown")
                .with_time_spent_hours(32.0)
                .with_stage("done")
                .build(),
            
            DomainTaskBuilder.domain_task_for_ui_conversion()
                .with_story_points(2.0)
                .assigned_to("alice.johnson")
                .with_time_spent_hours(8.0)
                .with_stage("done")
                .build()
        ]