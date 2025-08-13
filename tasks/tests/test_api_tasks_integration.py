import unittest
from unittest.mock import AsyncMock
from typing import List, Optional

from tasks.app.domain.assignee_search_service import AssigneeSearchService
from tasks.app.domain.convertors.task_metadata_convertor import TaskMetadataPopulator
from tasks.app.domain.model.config import TasksConfig, WorkflowConfig
from tasks.app.domain.model.task import HierarchyTraversalCriteria, TaskSearchCriteria, Task
from tasks.app.domain.task_hierarchy_service import TaskHierarchyService
from tasks.tests.fixtures.task_builders import TaskBuilder
from tasks.tests.mocks.mock_task_repository import MockTaskRepository


class TestApiTasksIntegration(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.repository = MockTaskRepository()
        self.assignee_search_service = AssigneeSearchService()
        self.config = self._create_test_config()
        self.metadata_convertor = TaskMetadataPopulator(self.config.workflow)
        
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
            stages={"development": ["In Progress", "Development"], "qa": ["Testing"], "done": ["Done", "Completed"]},
            recently_finished_tasks_days=30
        )
        
        return TestTasksConfig(workflow=workflow)
    
    async def test_shouldLoadCompleteHierarchyWhenJiraProviderReturnsFullTaskTrees(self):
        # Given
        complete_hierarchy = self._create_complete_three_level_hierarchy()
        self.repository.mock.find_all.return_value = [complete_hierarchy]
        task_ids = ["EPIC-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_complete_three_level_hierarchy_loaded(epic)
    
    async def test_shouldLoadHierarchyIncrementallyWhenAzureProviderReturnsDirectChildrenOnly(self):
        # Given
        requested_before = set()
        
        def mock_incremental_loading(search_criteria, enrichment=None):
            nonlocal requested_before
            requested_ids = search_criteria.id_filter if search_criteria else []
            results = []
            
            for task_id in requested_ids:
                if task_id == "EPIC-001":
                    if task_id in requested_before:
                        epic = self._create_epic_with_level_1_children_only()
                        results.append(epic)
                    else:
                        requested_before.add(task_id)
                        epic = self._create_epic_root_only()
                        results.append(epic)
                elif task_id == "STORY-001":
                    results.extend(self._create_story_001_with_children())
                elif task_id == "STORY-002":
                    results.extend(self._create_story_002_with_children())
            
            return results
        
        self.repository.mock.find_all.side_effect = mock_incremental_loading
        task_ids = ["EPIC-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_complete_three_level_hierarchy_loaded(epic)
    
    async def test_shouldBatchLoadSiblingsWhenRepositoryOptimizationIsEnabled(self):
        # Given
        def mock_batched_sibling_loading(search_criteria, enrichment=None):
            if not search_criteria or not search_criteria.id_filter:
                return [self._create_epic_with_multiple_siblings_root()]
            
            requested_ids = search_criteria.id_filter
            
            if len(requested_ids) > 1 and all(id.startswith("SIBLING-") for id in requested_ids):
                return self._create_all_siblings_with_children(requested_ids)
            elif "MULTI-001" in requested_ids:
                return [self._create_epic_with_three_sibling_stories()]
            
            return []
        
        self.repository.mock.find_all.side_effect = mock_batched_sibling_loading
        task_ids = ["MULTI-001"]
        criteria = HierarchyTraversalCriteria(max_depth=2)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_all_three_siblings_loaded(epic)
    
    async def test_shouldRespectDepthLimitWhenRepositoryReturnsDeepHierarchies(self):
        # Given
        seven_level_hierarchy = self._create_seven_level_hierarchy()
        self.repository.mock.find_all.return_value = [seven_level_hierarchy]
        task_ids = ["EPIC-001"]
        criteria = HierarchyTraversalCriteria(max_depth=4)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_hierarchy_depth_exactly(epic, 4)
    
    async def test_shouldIntegrateAssigneeSearchWhenHierarchyLoadingProvidesAssigneeData(self):
        # Given
        epic = self._create_epic_with_assignee_data()
        self.repository.mock.find_all.return_value = [epic]
        task_ids = ["TEAM-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=2)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        alice = self.assignee_search_service.get_assignee_by_id("alice.senior")
        self.assertIsNotNone(alice)
    
    async def test_shouldIntegrateMetadataConvertorWhenHierarchyLoadingProvidesStatusData(self):
        # Given
        epic = self._create_epic_with_status_metadata()
        self.repository.mock.find_all.return_value = [epic]
        task_ids = ["STATUS-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=2)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self.assertEqual(epic.stage, "development")
    
    # Test data creation methods
    
    def _create_complete_three_level_hierarchy(self) -> Task:
        task_1 = TaskBuilder("TASK-001", "Task 1").with_story_points(3.0).in_progress().build()
        task_2 = TaskBuilder("TASK-002", "Task 2").with_story_points(5.0).build()
        task_3 = TaskBuilder("TASK-003", "Task 3").with_story_points(13.0).build()
        
        story_1 = (TaskBuilder("STORY-001", "Story 1")
                   .with_story_points(8.0)
                   .in_progress()
                   .with_child_tasks(task_1, task_2)
                   .build())
        
        story_2 = (TaskBuilder("STORY-002", "Story 2")
                   .with_story_points(13.0)
                   .in_progress()
                   .with_child_tasks(task_3)
                   .build())
        
        return (TaskBuilder("EPIC-001", "Epic Root")
                .with_story_points(21.0)
                .in_progress()
                .with_child_tasks(story_1, story_2)
                .build())
    
    def _create_epic_root_only(self) -> Task:
        return TaskBuilder("EPIC-001", "Epic Root").with_story_points(21.0).in_progress().build()
    
    def _create_epic_with_level_1_children_only(self) -> Task:
        story_1 = TaskBuilder("STORY-001", "Story 1").with_story_points(8.0).in_progress().build()
        story_2 = TaskBuilder("STORY-002", "Story 2").with_story_points(13.0).in_progress().build()
        
        return (TaskBuilder("EPIC-001", "Epic Root")
                .with_story_points(21.0)
                .in_progress()
                .with_child_tasks(story_1, story_2)
                .build())
    
    def _create_story_001_with_children(self) -> List[Task]:
        task_1 = TaskBuilder("TASK-001", "Task 1").with_story_points(3.0).in_progress().build()
        task_2 = TaskBuilder("TASK-002", "Task 2").with_story_points(5.0).build()
        
        story_1 = (TaskBuilder("STORY-001", "Story 1")
                   .with_story_points(8.0)
                   .in_progress()
                   .with_child_tasks(task_1, task_2)
                   .build())
        
        return [story_1]
    
    def _create_story_002_with_children(self) -> List[Task]:
        task_3 = TaskBuilder("TASK-003", "Task 3").with_story_points(13.0).build()
        
        story_2 = (TaskBuilder("STORY-002", "Story 2")
                   .with_story_points(13.0)
                   .in_progress()
                   .with_child_tasks(task_3)
                   .build())
        
        return [story_2]
    
    def _create_epic_with_multiple_siblings_root(self) -> Task:
        return TaskBuilder("MULTI-001", "Multi Sibling Epic").with_story_points(30.0).build()
    
    def _create_epic_with_three_sibling_stories(self) -> Task:
        sibling_1 = TaskBuilder("SIBLING-001", "Sibling Story 1").with_story_points(10.0).build()
        sibling_2 = TaskBuilder("SIBLING-002", "Sibling Story 2").with_story_points(10.0).build()
        sibling_3 = TaskBuilder("SIBLING-003", "Sibling Story 3").with_story_points(10.0).build()
        
        return (TaskBuilder("MULTI-001", "Multi Sibling Epic")
                .with_story_points(30.0)
                .with_child_tasks(sibling_1, sibling_2, sibling_3)
                .build())
    
    def _create_all_siblings_with_children(self, requested_ids: List[str]) -> List[Task]:
        results = []
        for sibling_id in requested_ids:
            if sibling_id == "SIBLING-001":
                child = TaskBuilder("SUB-001", "Subtask 1").with_story_points(5.0).build()
                sibling = (TaskBuilder("SIBLING-001", "Sibling Story 1")
                          .with_story_points(10.0)
                          .with_child_tasks(child)
                          .build())
                results.append(sibling)
            elif sibling_id == "SIBLING-002":
                child = TaskBuilder("SUB-002", "Subtask 2").with_story_points(5.0).build()
                sibling = (TaskBuilder("SIBLING-002", "Sibling Story 2")
                          .with_story_points(10.0)
                          .with_child_tasks(child)
                          .build())
                results.append(sibling)
            elif sibling_id == "SIBLING-003":
                child = TaskBuilder("SUB-003", "Subtask 3").with_story_points(5.0).build()
                sibling = (TaskBuilder("SIBLING-003", "Sibling Story 3")
                          .with_story_points(10.0)
                          .with_child_tasks(child)
                          .build())
                results.append(sibling)
        return results
    
    def _create_seven_level_hierarchy(self):
        level_7 = TaskBuilder("EPIC-L7", "Level 7 Task").with_story_points(1.0).build()
        level_6 = TaskBuilder("EPIC-L6", "Level 6 Task").with_story_points(1.0).with_child_tasks(level_7).build()
        level_5 = TaskBuilder("EPIC-L5", "Level 5 Task").with_story_points(1.0).with_child_tasks(level_6).build()
        level_4 = TaskBuilder("EPIC-L4", "Level 4 Task").with_story_points(2.0).with_child_tasks(level_5).build()
        level_3 = TaskBuilder("EPIC-L3", "Level 3 Task").with_story_points(3.0).with_child_tasks(level_4).build()
        level_2 = TaskBuilder("EPIC-L2", "Level 2 Task").with_story_points(5.0).with_child_tasks(level_3).build()
        level_1 = TaskBuilder("EPIC-L1", "Level 1 Task").with_story_points(8.0).with_child_tasks(level_2).build()
        return TaskBuilder("EPIC-001", "Epic Root").with_story_points(13.0).with_child_tasks(level_1).build()
    
    def _create_epic_with_assignee_data(self) -> Task:
        child_with_assignee = (TaskBuilder("TEAM-002", "Child Task")
                              .assigned_to_senior_developer()
                              .with_story_points(5.0)
                              .build())
        
        return (TaskBuilder("TEAM-001", "Team Epic")
                .with_story_points(8.0)
                .with_child_tasks(child_with_assignee)
                .build())
    
    def _create_epic_with_status_metadata(self) -> Task:
        return (TaskBuilder("STATUS-001", "Status Epic")
                .with_original_status("In Progress")
                .with_story_points(5.0)
                .build())
    
    # Assertion methods
    
    def _assert_complete_three_level_hierarchy_loaded(self, epic: Task):
        self.assertEqual(epic.id, "EPIC-001")
        self.assertEqual(2, len(epic.child_tasks))
        
        story_1 = epic.child_tasks[0]
        story_2 = epic.child_tasks[1]
        
        self.assertEqual(story_1.id, "STORY-001")
        self.assertEqual(2, len(story_1.child_tasks))
        self.assertEqual(story_2.id, "STORY-002")
        self.assertEqual(1, len(story_2.child_tasks))
    
    def _assert_all_three_siblings_loaded(self, epic: Task):
        self.assertEqual(3, len(epic.child_tasks))
        sibling_ids = {child.id for child in epic.child_tasks}
        expected_ids = {"SIBLING-001", "SIBLING-002", "SIBLING-003"}
        self.assertEqual(sibling_ids, expected_ids)
    
    def _assert_hierarchy_depth_exactly(self, root_task, expected_depth):
        current = root_task
        for depth in range(1, expected_depth):
            self.assertIsNotNone(current.child_tasks, f"Missing children at depth {depth}")
            self.assertEqual(1, len(current.child_tasks), f"Expected single child at depth {depth}")
            current = current.child_tasks[0]
        
        self.assertIsNone(current.child_tasks, f"Task at depth {expected_depth} should have no children")


if __name__ == '__main__':
    unittest.main()