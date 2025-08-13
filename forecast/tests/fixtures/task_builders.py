from datetime import datetime
from typing import List, Optional

from sd_metrics_lib.utils.time import Duration, TimeUnit

from forecast.app.domain.model.task import Task, Assignment, Assignee, TimeTracking


class TaskBuilder:
    
    def __init__(self, task_id: str, title: str):
        self._id = task_id
        self._title = title
        self._story_points: Optional[float] = None
        self._assignee: Optional[Assignee] = None
        self._total_spent_time: Optional[Duration] = None
        self._child_tasks: List[Task] = []
        
    @classmethod
    def authentication_feature(cls) -> 'TaskBuilder':
        return cls("AUTH-123", "Implement user authentication")
    
    @classmethod
    def critical_bug(cls) -> 'TaskBuilder':
        return cls("BUG-456", "Fix critical login issue")
    
    @classmethod  
    def new_feature(cls) -> 'TaskBuilder':
        return cls("FEAT-789", "Add password reset functionality")
    
    @classmethod
    def epic_with_children(cls) -> 'TaskBuilder':
        return cls("EPIC-001", "User Management Epic")
    
    def with_story_points(self, points: float) -> 'TaskBuilder':
        self._story_points = points
        return self
    
    def assigned_to_senior_developer(self) -> 'TaskBuilder':
        self._assignee = Assignee(
            id="john.doe",
            display_name="John Doe (Senior Developer)",
            avatar_url="https://example.com/avatar/john.jpg"
        )
        return self
    
    def assigned_to_junior_developer(self) -> 'TaskBuilder':
        self._assignee = Assignee(
            id="jane.smith",
            display_name="Jane Smith (Junior Developer)", 
            avatar_url="https://example.com/avatar/jane.jpg"
        )
        return self
    
    def with_no_time_spent(self) -> 'TaskBuilder':
        self._total_spent_time = None
        return self
    
    def with_time_spent_hours(self, hours: float) -> 'TaskBuilder':
        self._total_spent_time = Duration.of(hours, TimeUnit.HOUR)
        return self
    
    def with_time_spent_days(self, days: float) -> 'TaskBuilder':
        self._total_spent_time = Duration.of(days, TimeUnit.DAY)
        return self
    
    def with_child_tasks(self, *child_tasks: Task) -> 'TaskBuilder':
        self._child_tasks = list(child_tasks)
        return self
    
    def build(self) -> Task:
        assignment = Assignment(assignee=self._assignee) if self._assignee else Assignment()
        time_tracking = TimeTracking(total_spent_time=self._total_spent_time) if self._total_spent_time else TimeTracking()
        
        return Task(
            id=self._id,
            title=self._title,
            story_points=self._story_points,
            assignment=assignment,
            time_tracking=time_tracking,
            child_tasks=self._child_tasks if self._child_tasks else None
        )


class BusinessScenarios:
    
    @staticmethod
    def green_health_task() -> Task:
        return (TaskBuilder.authentication_feature()
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(10.0)
                .build())
    
    @staticmethod
    def yellow_health_task() -> Task:
        return (TaskBuilder.critical_bug()
                .with_story_points(3.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(15.0)
                .build())
    
    @staticmethod
    def orange_health_task() -> Task:
        return (TaskBuilder.new_feature()
                .with_story_points(2.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(20.0)
                .build())
    
    @staticmethod
    def critical_red_health_task() -> Task:
        return (TaskBuilder.authentication_feature()
                .with_story_points(1.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(25.0)
                .build())
    
    @staticmethod
    def task_without_story_points() -> Task:
        return (TaskBuilder.critical_bug()
                .assigned_to_senior_developer()
                .with_time_spent_hours(5.0)
                .build())
    
    @staticmethod
    def task_without_time_tracking() -> Task:
        return (TaskBuilder.new_feature()
                .with_story_points(8.0)
                .assigned_to_senior_developer()
                .with_no_time_spent()
                .build())
    
    @staticmethod
    def parent_task_with_children() -> Task:
        child1 = (TaskBuilder("AUTH-124", "Design login UI")
                  .with_story_points(3.0)
                  .assigned_to_senior_developer()
                  .with_time_spent_hours(12.0)
                  .build())
        
        child2 = (TaskBuilder("AUTH-125", "Implement authentication API")
                  .with_story_points(5.0)
                  .assigned_to_junior_developer()
                  .with_time_spent_hours(18.0)
                  .build())
        
        return (TaskBuilder.epic_with_children()
                .with_story_points(10.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(5.0)
                .with_child_tasks(child1, child2)
                .build())