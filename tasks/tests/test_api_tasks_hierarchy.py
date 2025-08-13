import unittest
from unittest.mock import AsyncMock

from tasks.app.domain.assignee_search_service import AssigneeSearchService
from tasks.app.domain.convertors.task_metadata_convertor import TaskMetadataPopulator
from tasks.app.domain.model.config import TasksConfig, WorkflowConfig
from tasks.app.domain.model.task import HierarchyTraversalCriteria
from tasks.app.domain.task_hierarchy_service import TaskHierarchyService
from tasks.tests.fixtures.task_builders import TaskBuilder
from tasks.tests.mocks.mock_task_repository import MockTaskRepository


class TestApiTasksHierarchy(unittest.IsolatedAsyncioTestCase):
    
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
    
    async def test_shouldExcludeDoneTasksWhenActiveSprintPlanningFocusesOnRemainingWork(self):
        # Given
        epic_with_mixed_status = self._create_epic_with_mixed_status_children()
        self.repository.mock.find_all.return_value = [epic_with_mixed_status]
        task_ids = ["SPRINT-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=True, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_no_done_tasks_in_hierarchy(epic)
    
    async def test_shouldExcludeDoneTasksWhenActiveSprintPlanningContainsOnlyActiveTasks(self):
        # Given
        epic_with_mixed_status = self._create_epic_with_mixed_status_children()
        self.repository.mock.find_all.return_value = [epic_with_mixed_status]
        task_ids = ["SPRINT-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=True, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_contains_only_active_tasks(epic)
    
    async def test_shouldIncludeDoneTasksWhenRetrospectiveAnalysisNeedsCompleteHistory(self):
        # Given
        epic_with_mixed_status = self._create_epic_with_mixed_status_children()
        self.repository.mock.find_all.return_value = [epic_with_mixed_status]
        task_ids = ["SPRINT-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_contains_done_tasks(epic)
    
    async def test_shouldIncludeDoneTasksWhenRetrospectiveAnalysisShowsAllStatusTypes(self):
        # Given
        epic_with_mixed_status = self._create_epic_with_mixed_status_children()
        self.repository.mock.find_all.return_value = [epic_with_mixed_status]
        task_ids = ["SPRINT-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=False, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_contains_all_status_types(epic)
    
    async def test_shouldExcludeDoneBranchesWhenCapacityPlanningIgnoresCompletedWork(self):
        # Given
        epic_with_done_parent_active_children = self._create_epic_with_done_parent_active_children()
        self.repository.mock.find_all.return_value = [epic_with_done_parent_active_children]
        task_ids = ["CAPACITY-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=True, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_done_branch_excluded_completely_with_children(epic)
    
    async def test_shouldExcludeEntireBranchWhenParentDoneInFocusedWorkView(self):
        # Given
        epic_with_done_branch = self._create_epic_with_done_parent_branch()
        self.repository.mock.find_all.return_value = [epic_with_done_branch]
        task_ids = ["FOCUS-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=True, max_depth=4)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_done_branch_excluded_completely(epic)
    
    async def test_shouldPreserveActiveBranchWhenFocusedWorkViewFiltersCompletedWork(self):
        # Given
        epic_with_done_branch = self._create_epic_with_done_parent_branch()
        self.repository.mock.find_all.return_value = [epic_with_done_branch]
        task_ids = ["FOCUS-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=True, max_depth=4)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_active_branch_preserved(epic)
    
    async def test_shouldRespectDepthLimitWhenComplexEpicHasManyLevels(self):
        # Given
        deep_epic_with_mixed_status = self._create_deep_epic_with_mixed_status()
        self.repository.mock.find_all.return_value = [deep_epic_with_mixed_status]
        task_ids = ["COMPLEX-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=True, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_depth_limited_to_three(epic)
    
    async def test_shouldPreserveMixedActiveStatusesWhenDepthLimitingApplied(self):
        # Given
        deep_epic_with_mixed_status = self._create_deep_epic_with_mixed_status()
        self.repository.mock.find_all.return_value = [deep_epic_with_mixed_status]
        task_ids = ["COMPLEX-001"]
        criteria = HierarchyTraversalCriteria(exclude_done_tasks=True, max_depth=3)
        
        # When
        result = await self.task_hierarchy_service.get_tasks_with_full_hierarchy(task_ids, criteria)
        
        # Then
        epic = result[0]
        self._assert_mixed_active_statuses_preserved(epic)
    
    def _create_epic_with_mixed_status_children(self):
        done_task = (TaskBuilder("SPRINT-002", "Completed Feature")
                     .with_story_points(5.0)
                     .completed()
                     .build())
        
        in_progress_task = (TaskBuilder("SPRINT-003", "Current Development")
                           .with_story_points(3.0)
                           .in_progress()
                           .build())
        
        todo_task = (TaskBuilder("SPRINT-004", "Planned Work")
                    .with_story_points(2.0)
                    .build())
        
        return (TaskBuilder("SPRINT-001", "Sprint Epic")
                .with_story_points(10.0)
                .in_progress()
                .with_child_tasks(done_task, in_progress_task, todo_task)
                .build())
    
    def _create_epic_with_done_parent_active_children(self):
        active_child_1 = (TaskBuilder("CAPACITY-002", "Active Sub-task 1")
                          .with_story_points(2.0)
                          .in_progress()
                          .build())
        
        active_child_2 = (TaskBuilder("CAPACITY-003", "Active Sub-task 2")
                          .with_story_points(3.0)
                          .build())
        
        done_parent = (TaskBuilder("CAPACITY-004", "Completed Parent")
                      .with_story_points(5.0)
                      .completed()
                      .with_child_tasks(active_child_1, active_child_2)
                      .build())
        
        return (TaskBuilder("CAPACITY-001", "Capacity Planning Epic")
                .with_story_points(10.0)
                .in_progress()
                .with_child_tasks(done_parent)
                .build())
    
    def _create_epic_with_done_parent_branch(self):
        done_child = (TaskBuilder("FOCUS-004", "Completed Sub-task")
                     .with_story_points(2.0)
                     .completed()
                     .build())
        
        done_branch = (TaskBuilder("FOCUS-002", "Completed Feature Branch")
                      .with_story_points(5.0)
                      .completed()
                      .with_child_tasks(done_child)
                      .build())
        
        active_child = (TaskBuilder("FOCUS-005", "Active Sub-task")
                       .with_story_points(3.0)
                       .in_progress()
                       .build())
        
        active_branch = (TaskBuilder("FOCUS-003", "Active Feature Branch")
                        .with_story_points(8.0)
                        .in_progress()
                        .with_child_tasks(active_child)
                        .build())
        
        return (TaskBuilder("FOCUS-001", "Focus Planning Epic")
                .with_story_points(15.0)
                .in_progress()
                .with_child_tasks(done_branch, active_branch)
                .build())
    
    def _create_deep_epic_with_mixed_status(self):
        level_4_done = (TaskBuilder("COMPLEX-005", "Deep Done Task")
                       .with_story_points(1.0)
                       .completed()
                       .build())
        
        level_4_active = (TaskBuilder("COMPLEX-006", "Deep Active Task")
                         .with_story_points(1.0)
                         .in_progress()
                         .build())
        
        level_3_mixed = (TaskBuilder("COMPLEX-004", "Level 3 Mixed")
                        .with_story_points(2.0)
                        .in_progress()
                        .with_child_tasks(level_4_done, level_4_active)
                        .build())
        
        level_2_active = (TaskBuilder("COMPLEX-003", "Level 2 Active")
                         .with_story_points(3.0)
                         .in_progress()
                         .with_child_tasks(level_3_mixed)
                         .build())
        
        level_1_todo = (TaskBuilder("COMPLEX-002", "Level 1 Todo")
                       .with_story_points(5.0)
                       .with_child_tasks(level_2_active)
                       .build())
        
        return (TaskBuilder("COMPLEX-001", "Complex Epic")
                .with_story_points(8.0)
                .in_progress()
                .with_child_tasks(level_1_todo)
                .build())
    
    def _assert_no_done_tasks_in_hierarchy(self, root_task):
        def check_no_done_tasks(task):
            if task.status is not None:
                self.assertNotEqual(task.status.value, "done", f"Found done task {task.id} when excluded")
            if task.child_tasks:
                for child in task.child_tasks:
                    check_no_done_tasks(child)
        
        check_no_done_tasks(root_task)
    
    def _assert_contains_only_active_tasks(self, root_task):
        def check_active_only(task):
            if task.status is not None:
                self.assertIn(task.status.value, ["todo", "in_progress"], 
                             f"Task {task.id} should be active status")
            if task.child_tasks:
                for child in task.child_tasks:
                    check_active_only(child)
        
        check_active_only(root_task)
    
    def _assert_contains_done_tasks(self, root_task):
        found_done_task = False
        
        def check_for_done_tasks(task):
            nonlocal found_done_task
            if task.status is not None and task.status.value == "done":
                found_done_task = True
            if task.child_tasks:
                for child in task.child_tasks:
                    check_for_done_tasks(child)
        
        check_for_done_tasks(root_task)
        self.assertTrue(found_done_task, "Expected to find at least one done task in hierarchy")
    
    def _assert_contains_all_status_types(self, root_task):
        found_statuses = set()
        
        def collect_statuses(task):
            if task.status is not None:
                found_statuses.add(task.status.value)
            if task.child_tasks:
                for child in task.child_tasks:
                    collect_statuses(child)
        
        collect_statuses(root_task)
        
        expected_statuses = {"todo", "in_progress", "done"}
        self.assertTrue(expected_statuses.issubset(found_statuses), 
                       f"Expected all status types, found: {found_statuses}")
    
    def _assert_done_branch_excluded_completely_with_children(self, root_task):
        self.assertEqual(root_task.id, "CAPACITY-001")
        
        def check_no_capacity_004_branch(task):
            self.assertNotEqual(task.id, "CAPACITY-004", "Done parent should be excluded")
            self.assertNotEqual(task.id, "CAPACITY-002", "Children of done parent should be excluded")
            self.assertNotEqual(task.id, "CAPACITY-003", "Children of done parent should be excluded")
            if task.child_tasks:
                for child in task.child_tasks:
                    check_no_capacity_004_branch(child)
        
        check_no_capacity_004_branch(root_task)
    
    def _assert_done_branch_excluded_completely(self, root_task):
        def check_no_focus_002_branch(task):
            self.assertNotEqual(task.id, "FOCUS-002", "Done branch should be excluded")
            self.assertNotEqual(task.id, "FOCUS-004", "Done branch children should be excluded")
            if task.child_tasks:
                for child in task.child_tasks:
                    check_no_focus_002_branch(child)
        
        check_no_focus_002_branch(root_task)
    
    def _assert_active_branch_preserved(self, root_task):
        found_active_branch = False
        
        def check_for_active_branch(task):
            nonlocal found_active_branch
            if task.id == "FOCUS-003":
                found_active_branch = True
            if task.child_tasks:
                for child in task.child_tasks:
                    check_for_active_branch(child)
        
        check_for_active_branch(root_task)
        self.assertTrue(found_active_branch, "Active branch should be preserved")
    
    def _assert_depth_limited_to_three(self, root_task):
        def check_max_depth(task, current_depth):
            self.assertLessEqual(current_depth, 3, f"Task {task.id} exceeds max depth of 3")
            if task.child_tasks:
                for child in task.child_tasks:
                    check_max_depth(child, current_depth + 1)
        
        check_max_depth(root_task, 1)
    
    def _assert_mixed_active_statuses_preserved(self, root_task):
        found_statuses = set()
        
        def collect_statuses(task):
            if task.status is not None:
                found_statuses.add(task.status.value)
            if task.child_tasks:
                for child in task.child_tasks:
                    collect_statuses(child)
        
        collect_statuses(root_task)
        
        expected_active_statuses = {"todo", "in_progress"}
        self.assertTrue(expected_active_statuses.issubset(found_statuses), 
                       f"Expected mixed active statuses, found: {found_statuses}")
        self.assertNotIn("done", found_statuses, "Should not contain done tasks")


if __name__ == '__main__':
    unittest.main()