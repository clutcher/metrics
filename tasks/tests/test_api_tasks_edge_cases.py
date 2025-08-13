import unittest
from unittest.mock import AsyncMock

from tasks.app.domain.assignee_search_service import AssigneeSearchService
from tasks.app.domain.convertors.task_metadata_convertor import TaskMetadataPopulator
from tasks.app.domain.model.config import TasksConfig, WorkflowConfig
from tasks.app.domain.model.task import TaskSearchCriteria, HierarchyTraversalCriteria
from tasks.app.domain.task_search_service import TaskSearchService
from tasks.app.domain.task_hierarchy_service import TaskHierarchyService
from tasks.tests.fixtures.task_builders import BusinessScenarios, TaskBuilder
from tasks.tests.mocks.mock_task_repository import MockTaskRepository


class TestApiTasksEdgeCases(unittest.IsolatedAsyncioTestCase):
    
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
        
        self.task_hierarchy_service = TaskHierarchyService(
            repository=self.repository,
            task_config=self.config,
            assignee_search_service=self.assignee_search_service,
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
    
    async def test_shouldReturnEmptyResultsWhenRepositoryReturnsNoTasks(self):
        # Given
        self.repository.mock.find_all.return_value = []
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(0, len(result))
    
    async def test_shouldReturnEmptyResultsWhenSearchCriteriaMatchNoExistingTasks(self):
        # Given
        self.repository.mock.find_all.return_value = []
        criteria = TaskSearchCriteria(status_filter=["Non-existent Status"])
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        self.assertEqual(0, len(result))
    
    async def test_shouldHandleTasksWithoutStoryPointsWhenPlanningDataIncomplete(self):
        # Given
        tasks_without_points = [BusinessScenarios.task_without_story_points()]
        self.repository.mock.find_all.return_value = tasks_without_points
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertIsNone(task.story_points)
    
    async def test_shouldHandleTasksWithoutAssigneeDataWhenTeamAssignmentIncomplete(self):
        # Given
        task_without_assignee = (TaskBuilder.research_spike()
                                 .with_no_time_spent()
                                 .build())
        task_without_assignee.assignment.assignee = None
        task_without_assignee.time_tracking.spent_time_by_assignee = None
        self.repository.mock.find_all.return_value = [task_without_assignee]
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertIsNone(task.assignment.assignee)
    
    async def test_shouldHandleTasksWithoutTimeTrackingWhenDataCollectionIncomplete(self):
        # Given
        task_without_time = (TaskBuilder.research_spike()
                            .with_no_time_spent()
                            .build())
        self.repository.mock.find_all.return_value = [task_without_time]
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertIsNone(task.time_tracking.total_spent_time)
    
    async def test_shouldHandleEmptyTaskListWhenAssigneeSearchCachePopulationRuns(self):
        # Given
        empty_tasks = []
        self.assignee_search_service.populate_assignee_cache_from_tasks(empty_tasks)
        
        # When
        result = self.assignee_search_service.get_assignee_by_id("any.assignee")
        
        # Then
        self.assertIsNone(result)
    
    async def test_shouldHandleUnknownAssigneeIdWhenCacheDoesNotContainRequestedAssignee(self):
        # Given
        assignee_id = "unknown.developer"
        
        # When
        result = self.assignee_search_service.get_assignee_by_id(assignee_id)
        
        # Then
        self.assertIsNone(result)
    
    async def test_shouldHandleTasksWithNullOriginalStatusWhenStatusMappingFails(self):
        # Given
        task = (TaskBuilder.critical_production_bug()
                .with_original_status("")
                .build())
        task.system_metadata.original_status = None
        tasks = [task]
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertEqual(task.status.value, "todo")
    
    async def test_shouldHandleTasksWithUnknownOriginalStatusWhenStatusMappingEncountersInvalidData(self):
        # Given
        task = (TaskBuilder.research_spike()
                .with_original_status("Unknown Status")
                .build())
        tasks = [task]
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        
        # When
        result = await self.task_search_service.search(criteria)
        
        # Then
        task = result[0]
        self.assertEqual(task.status.value, "todo")
    
    async def test_shouldHandleEmptyHierarchyWhenRepositoryReturnsTasksWithoutChildren(self):
        # Given
        task_without_children = TaskBuilder.sprint_story().build()
        self.repository.mock.find_all.return_value = [task_without_children]
        task_ids = ["PROJ-123"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        task = result[0]
        self.assertIsNone(task.child_tasks)
    
    async def test_shouldHandleMaxDepthZeroWhenHierarchyTraversalLimitedToRootOnly(self):
        # Given
        epic_without_children = TaskBuilder("EPIC-001", "Epic with Children").build()
        self.repository.mock.find_all.return_value = [epic_without_children]
        task_ids = ["EPIC-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=0)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        task = result[0]
        self.assertIsNone(task.child_tasks)
    
    async def test_shouldHandleVeryLargeMaxDepthWhenHierarchyTraversalRequestsExcessiveDepth(self):
        # Given
        simple_task = TaskBuilder.sprint_story().build()
        self.repository.mock.find_all.return_value = [simple_task]
        task_ids = ["PROJ-123"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=1000)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        task = result[0]
        self.assertIsNone(task.child_tasks)
    
    async def test_shouldHandleEmptyTaskIdsListWhenHierarchyRequestContainsNoTargets(self):
        # Given
        task_ids = []
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        self.assertEqual(0, len(result))
    
    async def test_shouldHandleRepositoryExceptionWhenDataAccessFails(self):
        # Given
        self.repository.mock.find_all.side_effect = Exception("Database connection failed")
        criteria = TaskSearchCriteria()
        
        # When/Then
        with self.assertRaises(Exception):
            await self.task_search_service.search(criteria)
    
    def _create_epic_with_children(self):
        child_task = TaskBuilder("CHILD-001", "Child Task").build()
        return (TaskBuilder("EPIC-001", "Epic with Children")
                .with_child_tasks(child_task)
                .build())


if __name__ == '__main__':
    unittest.main()