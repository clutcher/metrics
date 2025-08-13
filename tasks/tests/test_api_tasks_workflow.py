import unittest
from unittest.mock import AsyncMock

from tasks.app.domain.assignee_search_service import AssigneeSearchService
from tasks.app.domain.convertors.task_metadata_convertor import TaskMetadataPopulator
from tasks.app.domain.model.config import TasksConfig, WorkflowConfig
from tasks.app.domain.model.task import TaskSearchCriteria
from tasks.app.domain.task_search_service import TaskSearchService
from tasks.tests.fixtures.task_builders import BusinessScenarios, TaskBuilder
from tasks.tests.mocks.mock_task_repository import MockTaskRepository


class TestApiTasksWorkflow(unittest.IsolatedAsyncioTestCase):
    
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
            stages={"development": ["In Progress", "Development"], "qa": ["Testing"], "done": ["Done", "Completed"]},
            recently_finished_tasks_days=30
        )
        
        return TestTasksConfig(workflow=workflow)
    
    def _create_repository_factory(self):
        def factory(worktime_extractor_type):
            return self.repository
        return factory
    
    async def test_shouldFilterByStatusWhenSprintWorkflowRequiresSpecificStages(self):
        # Given
        completed_tasks = BusinessScenarios.retrospective_completed_work()
        self.repository.mock.find_all.return_value = completed_tasks
        criteria = TaskSearchCriteria(status_filter=["Done", "Completed"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(2, len(result))
    
    async def test_shouldFilterByAssigneeWhenWorkflowFocusesOnIndividualContributions(self):
        # Given
        alice_tasks = [
            TaskBuilder.retrospective_completed_feature().assigned_to_senior_developer().build(),
            TaskBuilder.critical_production_bug().assigned_to_senior_developer().build()
        ]
        self.repository.mock.find_all.return_value = alice_tasks
        criteria = TaskSearchCriteria(assignee_filter=["alice.senior"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(2, len(result))
    
    async def test_shouldFilterByTeamWhenWorkflowFocusesOnTeamCapacity(self):
        # Given
        backend_tasks = [
            TaskBuilder.sprint_story().with_backend_team().with_story_points(5.0).build(),
            TaskBuilder.capacity_planning_task().with_backend_team().with_story_points(8.0).build()
        ]
        self.repository.mock.find_all.return_value = backend_tasks
        criteria = TaskSearchCriteria(team_filter=["backend-team"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(2, len(result))
    
    async def test_shouldCombineFiltersWhenWorkflowRequiresSpecificAssigneeAndStatus(self):
        # Given
        filtered_tasks = [
            TaskBuilder.capacity_planning_task()
                .assigned_to_senior_developer()
                .with_backend_team()
                .in_progress()
                .with_story_points(8.0)
                .build()
        ]
        self.repository.mock.find_all.return_value = filtered_tasks
        criteria = TaskSearchCriteria(
            status_filter=["In Progress"],
            team_filter=["backend-team"],
            assignee_filter=["alice.senior"]
        )
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(1, len(result))
    
    async def test_shouldSearchByTaskIdsWhenWorkflowRequiresSpecificTaskAnalysis(self):
        # Given
        tasks = [
            TaskBuilder.sprint_story().with_story_points(5.0).build(),
            TaskBuilder.critical_production_bug().with_story_points(3.0).build()
        ]
        self.repository.mock.find_all.return_value = tasks
        task_ids = ["PROJ-123", "PROJ-456"]
        
        # When
        result = await self.task_search_service.search_by_ids(task_ids)
        
        # Then
        self.assertEqual(2, len(result))
    
    


if __name__ == '__main__':
    unittest.main()