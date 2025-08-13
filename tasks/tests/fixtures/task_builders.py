from datetime import datetime, timedelta
from typing import List, Optional, Dict

from sd_metrics_lib.utils.time import Duration, TimeUnit

from tasks.app.domain.model.task import Task, Assignment, Assignee, TimeTracking, SystemMetadata, TaskStatus, MemberGroup


class TaskBuilder:
    
    def __init__(self, task_id: str, title: str):
        self._id = task_id
        self._title = title
        self._created_at = datetime(2024, 1, 1, 10, 0, 0)
        self._updated_at = datetime(2024, 1, 15, 14, 30, 0)
        self._story_points: Optional[float] = None
        self._assignee: Optional[Assignee] = None
        self._member_group: Optional[MemberGroup] = None
        self._total_spent_time: Optional[Duration] = None
        self._spent_time_by_assignee: Optional[Dict[str, Duration]] = None
        self._current_assignee_spent_time: Optional[Duration] = None
        self._child_tasks: List[Task] = []
        self._status: Optional[TaskStatus] = None
        self._stage: Optional[str] = None
        self._original_status = "To Do"
        self._project_key = "PROJ"
        self._url: Optional[str] = None
        self._child_tasks_count: Optional[int] = None
    
    @classmethod
    def sprint_story(cls) -> 'TaskBuilder':
        return cls("PROJ-123", "Implement user authentication system")
    
    @classmethod
    def critical_production_bug(cls) -> 'TaskBuilder':
        return cls("PROJ-456", "Fix critical payment gateway timeout")
    
    @classmethod
    def epic_parent_task(cls) -> 'TaskBuilder':
        return cls("PROJ-001", "User Management Epic")
    
    @classmethod
    def retrospective_completed_feature(cls) -> 'TaskBuilder':
        return cls("PROJ-789", "Add password reset functionality")
    
    @classmethod
    def capacity_planning_task(cls) -> 'TaskBuilder':
        return cls("PROJ-321", "Implement OAuth integration")
    
    @classmethod
    def research_spike(cls) -> 'TaskBuilder':
        return cls("PROJ-654", "Research database migration strategy")
    
    @classmethod
    def ui_enhancement(cls) -> 'TaskBuilder':
        return cls("PROJ-987", "Redesign dashboard navigation")
    
    @classmethod
    def technical_debt_cleanup(cls) -> 'TaskBuilder':
        return cls("PROJ-111", "Refactor legacy authentication code")
    
    @classmethod
    def performance_optimization(cls) -> 'TaskBuilder':
        return cls("PROJ-555", "Optimize database query performance")
    
    @classmethod
    def security_vulnerability_fix(cls) -> 'TaskBuilder':
        return cls("PROJ-666", "Patch SQL injection vulnerability")
    
    @classmethod
    def feature_enhancement(cls) -> 'TaskBuilder':
        return cls("PROJ-777", "Add advanced search filters")
    
    @classmethod
    def infrastructure_task(cls) -> 'TaskBuilder':
        return cls("PROJ-888", "Migrate to cloud infrastructure")
    
    @classmethod
    def documentation_update(cls) -> 'TaskBuilder':
        return cls("PROJ-999", "Update API documentation")
    
    def with_story_points(self, points: float) -> 'TaskBuilder':
        self._story_points = points
        return self
    
    def assigned_to_senior_developer(self) -> 'TaskBuilder':
        self._assignee = Assignee(
            id="alice.senior",
            display_name="Alice Thompson (Senior Developer)",
            avatar_url="https://company.com/avatars/alice.jpg"
        )
        return self
    
    def assigned_to_junior_developer(self) -> 'TaskBuilder':
        self._assignee = Assignee(
            id="bob.junior",
            display_name="Bob Wilson (Junior Developer)", 
            avatar_url="https://company.com/avatars/bob.jpg"
        )
        return self
    
    def assigned_to_team_lead(self) -> 'TaskBuilder':
        self._assignee = Assignee(
            id="charlie.lead",
            display_name="Charlie Davis (Team Lead)",
            avatar_url="https://company.com/avatars/charlie.jpg"
        )
        return self
    
    def assigned_to_member_group(self, group_id: str, group_name: str) -> 'TaskBuilder':
        self._member_group = MemberGroup(id=group_id, name=group_name)
        return self
    
    def with_backend_team(self) -> 'TaskBuilder':
        return self.assigned_to_member_group("backend-team", "Backend Development Team")
    
    def with_frontend_team(self) -> 'TaskBuilder':
        return self.assigned_to_member_group("frontend-team", "Frontend Development Team")
    
    def with_no_time_spent(self) -> 'TaskBuilder':
        self._total_spent_time = None
        self._spent_time_by_assignee = None
        self._current_assignee_spent_time = None
        return self
    
    def with_time_spent_hours(self, hours: float) -> 'TaskBuilder':
        self._total_spent_time = Duration.of(hours, TimeUnit.HOUR)
        if self._assignee:
            self._spent_time_by_assignee = {self._assignee.id: self._total_spent_time}
            self._current_assignee_spent_time = self._total_spent_time
        return self
    
    def with_time_spent_by_multiple_assignees(self, time_by_assignee: Dict[str, float]) -> 'TaskBuilder':
        self._spent_time_by_assignee = {}
        total_hours = 0.0
        for assignee_id, hours in time_by_assignee.items():
            duration = Duration.of(hours, TimeUnit.HOUR)
            self._spent_time_by_assignee[assignee_id] = duration
            total_hours += hours
        
        self._total_spent_time = Duration.of(total_hours, TimeUnit.HOUR)
        if self._assignee and self._assignee.id in self._spent_time_by_assignee:
            self._current_assignee_spent_time = self._spent_time_by_assignee[self._assignee.id]
        return self
    
    def with_child_tasks(self, *child_tasks: Task) -> 'TaskBuilder':
        self._child_tasks = list(child_tasks)
        self._child_tasks_count = len(child_tasks) if child_tasks else None
        return self
    
    def with_status(self, status: TaskStatus) -> 'TaskBuilder':
        self._status = status
        return self
    
    def with_stage(self, stage: str) -> 'TaskBuilder':
        self._stage = stage
        return self
    
    def with_original_status(self, original_status: str) -> 'TaskBuilder':
        self._original_status = original_status
        return self
    
    def in_progress(self) -> 'TaskBuilder':
        return self.with_status(TaskStatus.IN_PROGRESS).with_original_status("In Progress")
    
    def completed(self) -> 'TaskBuilder':
        return self.with_status(TaskStatus.DONE).with_original_status("Done")
    
    def blocked(self) -> 'TaskBuilder':
        return self.with_status(TaskStatus.BLOCKED).with_original_status("Blocked")
    
    def with_project_key(self, project_key: str) -> 'TaskBuilder':
        self._project_key = project_key
        return self
    
    def with_url(self, url: str) -> 'TaskBuilder':
        self._url = url
        return self
    
    def with_dates(self, created_at: datetime, updated_at: datetime) -> 'TaskBuilder':
        self._created_at = created_at
        self._updated_at = updated_at
        return self
    
    def created_last_week(self) -> 'TaskBuilder':
        now = datetime.now()
        created = now - timedelta(days=7)
        updated = now - timedelta(days=2)
        return self.with_dates(created, updated)
    
    def created_this_sprint(self) -> 'TaskBuilder':
        now = datetime.now()
        created = now - timedelta(days=10)
        updated = now - timedelta(hours=6)
        return self.with_dates(created, updated)
    
    def build(self) -> Task:
        assignment = Assignment(
            assignee=self._assignee,
            member_group=self._member_group
        )
        
        time_tracking = TimeTracking(
            total_spent_time=self._total_spent_time,
            spent_time_by_assignee=self._spent_time_by_assignee,
            current_assignee_spent_time=self._current_assignee_spent_time
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
            child_tasks_count=self._child_tasks_count,
            child_tasks=self._child_tasks if self._child_tasks else None
        )


class BusinessScenarios:
    
    @staticmethod
    def sprint_planning_backlog() -> List[Task]:
        return [
            TaskBuilder.sprint_story()
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .with_backend_team()
                .with_no_time_spent()
                .build(),
            
            TaskBuilder.capacity_planning_task()
                .with_story_points(8.0)
                .assigned_to_team_lead()
                .with_backend_team()
                .with_no_time_spent()
                .build(),
            
            TaskBuilder.ui_enhancement()
                .with_story_points(3.0)
                .assigned_to_junior_developer()
                .with_frontend_team()
                .with_no_time_spent()
                .build()
        ]
    
    @staticmethod
    def healthy_sprint_in_progress() -> List[Task]:
        """Sprint with good velocity and no blockers"""
        return [
            TaskBuilder.sprint_story()
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(15.0)
                .in_progress()
                .build(),
            
            TaskBuilder.ui_enhancement()
                .with_story_points(3.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(8.0)
                .in_progress()
                .build()
        ]
    
    @staticmethod
    def sprint_with_capacity_concerns() -> List[Task]:
        """Sprint showing team overcommitment and velocity issues"""
        return [
            TaskBuilder.critical_production_bug()
                .with_story_points(8.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(40.0)
                .in_progress()
                .build(),
            
            TaskBuilder.capacity_planning_task()
                .with_story_points(13.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(25.0)
                .in_progress()
                .build()
        ]
    
    @staticmethod
    def sprint_with_blocked_work() -> List[Task]:
        """Sprint with impediments affecting team productivity"""
        return [
            BusinessScenarios.blocked_critical_task(),
            
            TaskBuilder.research_spike()
                .with_story_points(2.0)
                .assigned_to_team_lead()
                .with_time_spent_hours(16.0)
                .with_status(TaskStatus.BLOCKED)
                .with_original_status("Blocked")
                .build()
        ]
    
    @staticmethod
    def green_health_project() -> Task:
        """Project showing healthy metrics across all indicators"""
        healthy_story = (TaskBuilder.sprint_story()
                        .with_story_points(5.0)
                        .assigned_to_senior_developer()
                        .with_time_spent_hours(18.0)
                        .in_progress()
                        .build())
        
        completed_story = (TaskBuilder.retrospective_completed_feature()
                          .with_story_points(3.0)
                          .assigned_to_junior_developer()
                          .with_time_spent_hours(12.0)
                          .completed()
                          .build())
        
        return (TaskBuilder.epic_parent_task()
               .with_story_points(8.0)
               .assigned_to_team_lead()
               .with_child_tasks(healthy_story, completed_story)
               .in_progress()
               .build())
    
    @staticmethod
    def red_health_project() -> Task:
        """Project showing concerning health metrics requiring attention"""
        blocked_story = BusinessScenarios.blocked_critical_task()
        
        overcommitted_story = (TaskBuilder.capacity_planning_task()
                              .with_story_points(13.0)
                              .assigned_to_senior_developer()
                              .with_time_spent_hours(60.0)
                              .in_progress()
                              .build())
        
        return (TaskBuilder.epic_parent_task()
               .with_story_points(21.0)
               .assigned_to_team_lead()
               .with_child_tasks(blocked_story, overcommitted_story)
               .in_progress()
               .build())
    
    @staticmethod
    def senior_developer_velocity_profile() -> List[Task]:
        """Tasks representing typical senior developer workload and velocity"""
        return [
            TaskBuilder.sprint_story()
                .with_story_points(8.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(24.0)
                .completed()
                .created_last_week()
                .build(),
            
            TaskBuilder.technical_debt_cleanup()
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(20.0)
                .completed()
                .created_last_week()
                .build(),
            
            TaskBuilder.critical_production_bug()
                .with_story_points(3.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(12.0)
                .in_progress()
                .created_this_sprint()
                .build()
        ]
    
    @staticmethod
    def junior_developer_velocity_profile() -> List[Task]:
        """Tasks representing typical junior developer workload and growth"""
        return [
            TaskBuilder.ui_enhancement()
                .with_story_points(3.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(16.0)
                .completed()
                .created_last_week()
                .build(),
            
            TaskBuilder.research_spike()
                .with_story_points(2.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(12.0)
                .completed()
                .created_last_week()
                .build(),
            
            TaskBuilder.capacity_planning_task()
                .with_story_points(5.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(18.0)
                .in_progress()
                .created_this_sprint()
                .build()
        ]
    
    @staticmethod
    def team_collaboration_intensive_work() -> List[Task]:
        """Tasks showing high collaboration and knowledge sharing"""
        return [
            BusinessScenarios.task_with_multiple_assignee_time_tracking(),
            
            TaskBuilder.research_spike()
                .with_story_points(8.0)
                .assigned_to_team_lead()
                .with_time_spent_by_multiple_assignees({
                    "charlie.lead": 10.0,
                    "alice.senior": 15.0,
                    "bob.junior": 8.0
                })
                .in_progress()
                .build()
        ]
    
    @staticmethod
    def retrospective_completed_work() -> List[Task]:
        return [
            TaskBuilder.retrospective_completed_feature()
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(20.0)
                .completed()
                .created_last_week()
                .build(),
            
            TaskBuilder.technical_debt_cleanup()
                .with_story_points(2.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(8.0)
                .completed()
                .created_last_week()
                .build()
        ]
    
    @staticmethod
    def capacity_planning_active_work() -> List[Task]:
        return [
            TaskBuilder.critical_production_bug()
                .with_story_points(3.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(12.0)
                .in_progress()
                .created_this_sprint()
                .build(),
            
            TaskBuilder.research_spike()
                .with_story_points(1.0)
                .assigned_to_team_lead()
                .with_time_spent_hours(6.0)
                .in_progress()
                .created_this_sprint()
                .build()
        ]
    
    @staticmethod
    def epic_with_child_hierarchy() -> Task:
        child1 = (TaskBuilder("PROJ-002", "Design user login interface")
                  .with_story_points(3.0)
                  .assigned_to_junior_developer()
                  .with_time_spent_hours(12.0)
                  .in_progress()
                  .build())
        
        child2 = (TaskBuilder("PROJ-003", "Implement authentication API endpoints")
                  .with_story_points(5.0)
                  .assigned_to_senior_developer()
                  .with_time_spent_hours(18.0)
                  .in_progress()
                  .build())
        
        child3 = (TaskBuilder("PROJ-004", "Add user registration validation")
                  .with_story_points(2.0)
                  .assigned_to_junior_developer()
                  .with_no_time_spent()
                  .build())
        
        return (TaskBuilder.epic_parent_task()
                .with_story_points(10.0)
                .assigned_to_team_lead()
                .with_time_spent_hours(5.0)
                .with_child_tasks(child1, child2, child3)
                .in_progress()
                .build())
    
    @staticmethod
    def task_without_story_points() -> Task:
        return (TaskBuilder.research_spike()
                .assigned_to_senior_developer()
                .with_time_spent_hours(4.0)
                .in_progress()
                .build())
    
    @staticmethod
    def task_with_multiple_assignee_time_tracking() -> Task:
        return (TaskBuilder.capacity_planning_task()
                .with_story_points(8.0)
                .assigned_to_team_lead()
                .with_time_spent_by_multiple_assignees({
                    "alice.senior": 15.0,
                    "bob.junior": 10.0,
                    "charlie.lead": 5.0
                })
                .in_progress()
                .build())
    
    @staticmethod
    def blocked_critical_task() -> Task:
        return (TaskBuilder.critical_production_bug()
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(8.0)
                .with_status(TaskStatus.BLOCKED)
                .with_original_status("Blocked")
                .build())
    
    @staticmethod
    def tasks_for_assignee_search() -> List[Task]:
        return [
            TaskBuilder.sprint_story()
                .assigned_to_senior_developer()
                .with_time_spent_hours(10.0)
                .build(),
            
            TaskBuilder.capacity_planning_task()
                .assigned_to_junior_developer()
                .with_time_spent_by_multiple_assignees({
                    "bob.junior": 8.0,
                    "alice.senior": 2.0
                })
                .build(),
            
            TaskBuilder.research_spike()
                .assigned_to_team_lead()
                .with_no_time_spent()
                .build()
        ]