import unittest
from unittest.mock import AsyncMock

from tasks.app.domain.assignee_search_service import AssigneeSearchService
from tasks.app.domain.convertors.task_metadata_convertor import TaskMetadataPopulator
from tasks.app.domain.model.config import TasksConfig, WorkflowConfig
from tasks.app.domain.model.task import TaskSearchCriteria, TaskStatus
from tasks.app.domain.task_search_service import TaskSearchService
from tasks.tests.fixtures.task_builders import BusinessScenarios, TaskBuilder
from tasks.tests.mocks.mock_task_repository import MockTaskRepository


class TestApiTasksHealth(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.repository = MockTaskRepository()
        self.assignee_search_service = AssigneeSearchService()
        self.config = self._create_test_config()
        self.metadata_convertor = TaskMetadataPopulator(self.config.workflow)
        
        self.task_search_service = TaskSearchService(
            repository=self.repository,
            task_config=self.config,
            assignee_search_service=self.assignee_search_service,
            repository_factory=self._create_repository_factory(),
            metadata_convertor=self.metadata_convertor
        )
    
    def _create_test_config(self) -> TasksConfig:
        from dataclasses import dataclass
        
        @dataclass(slots=True)
        class TestTasksConfig:
            workflow: WorkflowConfig
        
        workflow = WorkflowConfig(
            in_progress_status_codes=["In Progress", "Development", "Testing"],
            done_status_codes=["Done", "Completed", "Closed"],
            pending_status_codes=["To Do", "Open", "Backlog"],
            stages={"development": ["In Progress", "Development"], "qa": ["Testing"], "done": ["Done", "Completed"], "blocked": ["Blocked"]},
            recently_finished_tasks_days=30
        )
        
        return TestTasksConfig(workflow=workflow)
    
    def _create_repository_factory(self):
        def factory(worktime_extractor_type):
            return self.repository
        return factory
    
    async def test_shouldIdentifyHealthyTasksWhenSprintIsOnTrack(self):
        # Given
        healthy_tasks = [
            TaskBuilder.sprint_story()
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .with_time_spent_hours(8.0)
                .in_progress()
                .build()
        ]
        self.repository.mock.find_all.return_value = healthy_tasks
        criteria = TaskSearchCriteria(status_filter=["In Progress"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(1, len(result))
    
    async def test_shouldIdentifyHealthyTasksWhenTaskHasStoryPointsAndAssignment(self):
        # Given
        healthy_tasks = [
            TaskBuilder.capacity_planning_task()
                .with_story_points(3.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(4.0)
                .in_progress()
                .build()
        ]
        self.repository.mock.find_all.return_value = healthy_tasks
        criteria = TaskSearchCriteria(status_filter=["In Progress"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertIsNotNone(task.story_points)
    
    async def test_shouldIdentifyHealthyTasksWhenTaskHasTimeTracking(self):
        # Given
        healthy_tasks = [
            TaskBuilder.capacity_planning_task()
                .with_story_points(3.0)
                .assigned_to_junior_developer()
                .with_time_spent_hours(4.0)
                .in_progress()
                .build()
        ]
        self.repository.mock.find_all.return_value = healthy_tasks
        criteria = TaskSearchCriteria(status_filter=["In Progress"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertIsNotNone(task.time_tracking.total_spent_time)
    
    async def test_shouldIdentifyCompletedTasksWhenRetrospectiveAnalysisShowsSuccess(self):
        # Given
        completed_tasks = BusinessScenarios.retrospective_completed_work()
        self.repository.mock.find_all.return_value = completed_tasks
        criteria = TaskSearchCriteria(status_filter=["Done", "Completed"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(2, len(result))
    
    async def test_shouldIdentifyCompletedTasksWhenTasksHaveDoneStatus(self):
        # Given
        completed_tasks = BusinessScenarios.retrospective_completed_work()
        self.repository.mock.find_all.return_value = completed_tasks
        criteria = TaskSearchCriteria(status_filter=["Done", "Completed"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        for task in result:
            self.assertEqual(task.status, TaskStatus.DONE)
    
    async def test_shouldIdentifyBlockedTasksWhenSprintHasImpediments(self):
        # Given
        blocked_task = BusinessScenarios.blocked_critical_task()
        self.repository.mock.find_all.return_value = [blocked_task]
        criteria = TaskSearchCriteria(status_filter=["Blocked"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(1, len(result))
    
    async def test_shouldIdentifyBlockedTasksWhenTaskHasBlockedStage(self):
        # Given
        blocked_task = BusinessScenarios.blocked_critical_task()
        self.repository.mock.find_all.return_value = [blocked_task]
        criteria = TaskSearchCriteria(status_filter=["Blocked"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertEqual(task.stage, "blocked")
    
    async def test_shouldIdentifyUnestimatedTasksWhenPlanningNeedsAttention(self):
        # Given
        tasks_without_points = [BusinessScenarios.task_without_story_points()]
        self.repository.mock.find_all.return_value = tasks_without_points
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertIsNone(task.story_points)
    
    async def test_shouldTrackMultipleAssigneesWhenTeamCollaborationIsHigh(self):
        # Given
        multi_assignee_task = BusinessScenarios.task_with_multiple_assignee_time_tracking()
        self.repository.mock.find_all.return_value = [multi_assignee_task]
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertEqual(3, len(task.time_tracking.spent_time_by_assignee))
    
    async def test_shouldPopulateTaskMetadataWhenHealthAnalysisRequiresStageInformation(self):
        # Given
        tasks = [
            TaskBuilder.sprint_story()
                .with_original_status("In Progress")
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .build()
        ]
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        in_progress_task = result[0]
        self.assertEqual(in_progress_task.status, TaskStatus.IN_PROGRESS)
    
    async def test_shouldPopulateTaskStageWhenHealthAnalysisRequiresStageInformation(self):
        # Given
        tasks = [
            TaskBuilder.sprint_story()
                .with_original_status("In Progress")
                .with_story_points(5.0)
                .assigned_to_senior_developer()
                .build()
        ]
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        in_progress_task = result[0]
        self.assertEqual(in_progress_task.stage, "development")
    
    
    async def test_shouldValidateSprintBacklogWhenAllTasksHaveRequiredAttributes(self):
        # Given
        healthy_backlog = BusinessScenarios.sprint_planning_backlog()
        self.repository.mock.find_all.return_value = healthy_backlog
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(3, len(result))
    
    async def test_shouldValidateTaskEstimationWhenBacklogTasksHaveStoryPoints(self):
        # Given
        healthy_backlog = BusinessScenarios.sprint_planning_backlog()
        self.repository.mock.find_all.return_value = healthy_backlog
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        for task in result:
            self.assertGreater(task.story_points, 0.0)
    
    async def test_shouldValidateTaskAssignmentWhenBacklogTasksHaveAssignees(self):
        # Given
        healthy_backlog = BusinessScenarios.sprint_planning_backlog()
        self.repository.mock.find_all.return_value = healthy_backlog
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        for task in result:
            self.assertIsNotNone(task.assignment.assignee)
    
    async def test_shouldValidateTeamAssignmentWhenBacklogTasksHaveMemberGroups(self):
        # Given
        healthy_backlog = BusinessScenarios.sprint_planning_backlog()
        self.repository.mock.find_all.return_value = healthy_backlog
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        for task in result:
            self.assertIsNotNone(task.assignment.member_group)


if __name__ == '__main__':
    unittest.main()