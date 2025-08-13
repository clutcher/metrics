import unittest

from tasks.app.domain.assignee_search_service import AssigneeSearchService
from tasks.app.domain.model.task import Assignee
from tasks.tests.fixtures.task_builders import BusinessScenarios, TaskBuilder


class TestUnitAssigneeSearchService(unittest.TestCase):
    
    def setUp(self):
        self.assignee_search_service = AssigneeSearchService()
    
    def test_shouldReturnNullWhenAssigneeNotFoundInEmptyCache(self):
        # Given
        assignee_id = "unknown.developer"
        
        # When
        result = self.assignee_search_service.get_assignee_by_id(assignee_id)
        
        # Then
        self.assertIsNone(result)
    
    def test_shouldReturnAliceWhenFoundInCacheAfterPopulation(self):
        # Given
        tasks = BusinessScenarios.tasks_for_assignee_search()
        self.assignee_search_service.populate_assignee_cache_from_tasks(tasks)
        
        # When
        alice = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertIsNotNone(alice)
    
    def test_shouldReturnAliceDisplayNameWhenFoundInCache(self):
        # Given
        tasks = BusinessScenarios.tasks_for_assignee_search()
        self.assignee_search_service.populate_assignee_cache_from_tasks(tasks)
        
        # When
        alice = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(alice.display_name, "Alice Thompson (Senior Developer)")
    
    def test_shouldReturnBobWhenFoundInCacheAfterPopulation(self):
        # Given
        tasks = BusinessScenarios.tasks_for_assignee_search()
        self.assignee_search_service.populate_assignee_cache_from_tasks(tasks)
        
        # When
        bob = self.assignee_search_service.get_assignee_by_id("bob.junior")
        
        # Then
        self.assertIsNotNone(bob)
    
    def test_shouldReturnBobDisplayNameWhenFoundInCache(self):
        # Given
        tasks = BusinessScenarios.tasks_for_assignee_search()
        self.assignee_search_service.populate_assignee_cache_from_tasks(tasks)
        
        # When
        bob = self.assignee_search_service.get_assignee_by_id("bob.junior")
        
        # Then
        self.assertEqual(bob.display_name, "Bob Wilson (Junior Developer)")
    
    def test_shouldReturnCharlieWhenFoundInCacheAfterPopulation(self):
        # Given
        tasks = BusinessScenarios.tasks_for_assignee_search()
        self.assignee_search_service.populate_assignee_cache_from_tasks(tasks)
        
        # When
        charlie = self.assignee_search_service.get_assignee_by_id("charlie.lead")
        
        # Then
        self.assertIsNotNone(charlie)
    
    def test_shouldReturnCharlieDisplayNameWhenFoundInCache(self):
        # Given
        tasks = BusinessScenarios.tasks_for_assignee_search()
        self.assignee_search_service.populate_assignee_cache_from_tasks(tasks)
        
        # When
        charlie = self.assignee_search_service.get_assignee_by_id("charlie.lead")
        
        # Then
        self.assertEqual(charlie.display_name, "Charlie Davis (Team Lead)")
    
    def test_shouldPopulateAssigneeIdWhenTaskHasDirectAssignee(self):
        # Given
        task = (TaskBuilder.capacity_planning_task()
                .assigned_to_senior_developer()
                .with_time_spent_hours(10.0)
                .build())
        self.assignee_search_service.populate_assignee_cache_from_tasks([task])
        
        # When
        assignee = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(assignee.id, "alice.senior")
    
    def test_shouldPopulateAssigneeDisplayNameWhenTaskHasDirectAssignee(self):
        # Given
        task = (TaskBuilder.capacity_planning_task()
                .assigned_to_senior_developer()
                .with_time_spent_hours(10.0)
                .build())
        self.assignee_search_service.populate_assignee_cache_from_tasks([task])
        
        # When
        assignee = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(assignee.display_name, "Alice Thompson (Senior Developer)")
    
    def test_shouldPopulateAssigneeAvatarWhenTaskHasDirectAssignee(self):
        # Given
        task = (TaskBuilder.capacity_planning_task()
                .assigned_to_senior_developer()
                .with_time_spent_hours(10.0)
                .build())
        self.assignee_search_service.populate_assignee_cache_from_tasks([task])
        
        # When
        assignee = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(assignee.avatar_url, "https://company.com/avatars/alice.jpg")
    
    def test_shouldCreateFallbackAssigneeWhenTimeTrackingHasAssigneeId(self):
        # Given
        task = BusinessScenarios.task_with_multiple_assignee_time_tracking()
        self.assignee_search_service.populate_assignee_cache_from_tasks([task])
        
        # When
        alice = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(alice.display_name, "alice.senior")
    
    def test_shouldCreateFallbackAssigneeWithNullAvatarWhenTimeTrackingHasAssigneeId(self):
        # Given
        task = BusinessScenarios.task_with_multiple_assignee_time_tracking()
        self.assignee_search_service.populate_assignee_cache_from_tasks([task])
        
        # When
        alice = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertIsNone(alice.avatar_url)
    
    def test_shouldPopulateFromChildTasksWhenEpicHasChildHierarchy(self):
        # Given
        epic_task = BusinessScenarios.epic_with_child_hierarchy()
        self.assignee_search_service.populate_assignee_cache_from_tasks([epic_task])
        
        # When
        team_lead = self.assignee_search_service.get_assignee_by_id("charlie.lead")
        
        # Then
        self.assertIsNotNone(team_lead)
    
    def test_shouldPopulateChildAssigneeDisplayNameWhenEpicHasChildHierarchy(self):
        # Given
        epic_task = BusinessScenarios.epic_with_child_hierarchy()
        self.assignee_search_service.populate_assignee_cache_from_tasks([epic_task])
        
        # When
        senior_dev = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(senior_dev.display_name, "Alice Thompson (Senior Developer)")
    
    def test_shouldHandleEmptyTaskListGracefully(self):
        # Given
        empty_tasks = []
        
        # When
        self.assignee_search_service.populate_assignee_cache_from_tasks(empty_tasks)
        result = self.assignee_search_service.get_assignee_by_id("any.assignee")
        
        # Then
        self.assertIsNone(result)
    
    def test_shouldOverwriteExistingCacheEntryWhenUpdatedTaskProvided(self):
        # Given
        original_task = (TaskBuilder.sprint_story()
                         .assigned_to_senior_developer()
                         .build())
        self.assignee_search_service.populate_assignee_cache_from_tasks([original_task])
        original_result = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        updated_assignee = Assignee(
            id="alice.senior",
            display_name="Alice Thompson (Tech Lead)",
            avatar_url="https://company.com/avatars/alice-updated.jpg"
        )
        updated_task = (TaskBuilder.capacity_planning_task().build())
        updated_task.assignment.assignee = updated_assignee
        
        # When
        self.assignee_search_service.populate_assignee_cache_from_tasks([updated_task])
        updated_result = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(updated_result.display_name, "Alice Thompson (Tech Lead)")
    
    def test_shouldUpdateAvatarUrlWhenCacheEntryOverwritten(self):
        # Given
        original_task = (TaskBuilder.sprint_story()
                         .assigned_to_senior_developer()
                         .build())
        self.assignee_search_service.populate_assignee_cache_from_tasks([original_task])
        
        updated_assignee = Assignee(
            id="alice.senior",
            display_name="Alice Thompson (Tech Lead)",
            avatar_url="https://company.com/avatars/alice-updated.jpg"
        )
        updated_task = (TaskBuilder.capacity_planning_task().build())
        updated_task.assignment.assignee = updated_assignee
        
        # When
        self.assignee_search_service.populate_assignee_cache_from_tasks([updated_task])
        updated_result = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(updated_result.avatar_url, "https://company.com/avatars/alice-updated.jpg")
    
    def test_shouldIgnoreTasksWithoutAssigneeDataWhenPopulating(self):
        # Given
        task_without_assignee = (TaskBuilder.research_spike()
                                 .with_no_time_spent()
                                 .build())
        task_without_assignee.assignment.assignee = None
        task_without_assignee.time_tracking.spent_time_by_assignee = None
        
        # When
        self.assignee_search_service.populate_assignee_cache_from_tasks([task_without_assignee])
        result = self.assignee_search_service.get_assignee_by_id("any.assignee")
        
        # Then
        self.assertIsNone(result)
    
    def test_shouldPreferExplicitAssigneeWhenBothExplicitAndTimeTrackingExist(self):
        # Given
        explicit_assignee = Assignee(
            id="alice.senior",
            display_name="Alice Thompson (Explicit Senior Developer)",
            avatar_url="https://company.com/avatars/alice-explicit.jpg"
        )
        task = (TaskBuilder.capacity_planning_task()
                .with_time_spent_by_multiple_assignees({
                    "alice.senior": 10.0,
                    "bob.junior": 5.0
                })
                .build())
        task.assignment.assignee = explicit_assignee
        
        # When
        self.assignee_search_service.populate_assignee_cache_from_tasks([task])
        alice = self.assignee_search_service.get_assignee_by_id("alice.senior")
        
        # Then
        self.assertEqual(alice.display_name, "Alice Thompson (Explicit Senior Developer)")
    
    def test_shouldUseFallbackForNonExplicitAssigneeWhenBothExplicitAndTimeTrackingExist(self):
        # Given
        explicit_assignee = Assignee(
            id="alice.senior",
            display_name="Alice Thompson (Explicit Senior Developer)",
            avatar_url="https://company.com/avatars/alice-explicit.jpg"
        )
        task = (TaskBuilder.capacity_planning_task()
                .with_time_spent_by_multiple_assignees({
                    "alice.senior": 10.0,
                    "bob.junior": 5.0
                })
                .build())
        task.assignment.assignee = explicit_assignee
        
        # When
        self.assignee_search_service.populate_assignee_cache_from_tasks([task])
        bob = self.assignee_search_service.get_assignee_by_id("bob.junior")
        
        # Then
        self.assertEqual(bob.display_name, "bob.junior")


if __name__ == '__main__':
    unittest.main()