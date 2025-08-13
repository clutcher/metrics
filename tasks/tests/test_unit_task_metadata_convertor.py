import unittest

from tasks.app.domain.convertors.task_metadata_convertor import TaskMetadataPopulator
from tasks.app.domain.model.config import WorkflowConfig
from tasks.app.domain.model.task import TaskStatus
from tasks.tests.fixtures.task_builders import TaskBuilder, BusinessScenarios


class TestUnitTaskMetadataConvertor(unittest.TestCase):
    
    def setUp(self):
        self.workflow_config = WorkflowConfig(
            in_progress_status_codes=["In Progress", "Development", "Testing"],
            done_status_codes=["Done", "Completed", "Closed"],
            pending_status_codes=["To Do", "Open", "Backlog"],
            stages={
                "development": ["In Progress", "Development"],
                "qa": ["Testing", "Code Review"],
                "done": ["Done", "Completed", "Closed"],
                "backlog": ["To Do", "Open", "Backlog"]
            },
            recently_finished_tasks_days=30
        )
        self.metadata_convertor = TaskMetadataPopulator(self.workflow_config)
    
    def test_shouldMapInProgressTaskToDevelopmentStageForSprintWork(self):
        # Given
        task = (TaskBuilder.sprint_story()
                .with_original_status("In Progress")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task.stage, "development")
    
    def test_shouldMapDoneTaskToDoneStageForRetrospectiveAnalysis(self):
        # Given
        task = (TaskBuilder.retrospective_completed_feature()
                .with_original_status("Done")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.DONE)
        self.assertEqual(task.stage, "done")
    
    def test_shouldMapCompletedTaskToDoneStageForCapacityPlanningReview(self):
        # Given
        task = (TaskBuilder.technical_debt_cleanup()
                .with_original_status("Completed")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.DONE)
        self.assertEqual(task.stage, "done")
    
    def test_shouldMapTestingTaskToQAStageForInProgressStatus(self):
        # Given
        task = (TaskBuilder.ui_enhancement()
                .with_original_status("Testing")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task.stage, "qa")
    
    def test_shouldDefaultToTodoWithNullStageWhenOriginalStatusIsUnknown(self):
        # Given
        task = (TaskBuilder.research_spike()
                .with_original_status("Unknown Status")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertIsNone(task.stage)
    
    def test_shouldDefaultToTodoWithNullStageWhenOriginalStatusIsNull(self):
        # Given
        task = (TaskBuilder.critical_production_bug()
                .with_original_status("")
                .build())
        task.system_metadata.original_status = None
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertIsNone(task.stage)
    
    def test_shouldMapDevelopmentTaskToInProgressWithDevelopmentStage(self):
        # Given
        task = (TaskBuilder.capacity_planning_task()
                .with_original_status("Development")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task.stage, "development")
    
    def test_shouldMapCodeReviewTaskToTodoWithQAStage(self):
        # Given
        task = (TaskBuilder.ui_enhancement()
                .with_original_status("Code Review")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.stage, "qa")
    
    def test_shouldReturnCorrectTaskCountWhenProcessingMultipleTasks(self):
        # Given
        tasks = [
            TaskBuilder.sprint_story().with_original_status("In Progress").build(),
            TaskBuilder.retrospective_completed_feature().with_original_status("Done").build(),
            TaskBuilder.research_spike().with_original_status("Testing").build()
        ]
        
        # When
        result = self.metadata_convertor.populate_metadata_for_tasks(tasks)
        
        # Then
        self.assertEqual(3, len(result))
    
    def test_shouldMapAllTasksCorrectlyWhenProcessingMultipleTasksBatch(self):
        # Given
        tasks = [
            TaskBuilder.sprint_story().with_original_status("In Progress").build(),
            TaskBuilder.retrospective_completed_feature().with_original_status("Done").build()
        ]
        
        # When
        result = self.metadata_convertor.populate_metadata_for_tasks(tasks)
        
        # Then
        self.assertEqual(result[0].status, TaskStatus.IN_PROGRESS)
        self.assertEqual(result[0].stage, "development")
        self.assertEqual(result[1].status, TaskStatus.DONE)
        self.assertEqual(result[1].stage, "done")
    
    def test_shouldReturnEmptyListWhenProcessingEmptyTaskList(self):
        # Given
        empty_tasks = []
        
        # When
        result = self.metadata_convertor.populate_metadata_for_tasks(empty_tasks)
        
        # Then
        self.assertEqual(0, len(result))
    
    def test_shouldMapBacklogTaskToTodoWithBacklogStage(self):
        # Given
        task = (TaskBuilder.capacity_planning_task()
                .with_original_status("Backlog")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertEqual(task.stage, "backlog")
    
    def test_shouldMapClosedTaskToDoneStageForRetrospectiveReview(self):
        # Given
        task = (TaskBuilder.technical_debt_cleanup()
                .with_original_status("Closed")
                .build())
        
        # When
        self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertEqual(task.status, TaskStatus.DONE)
        self.assertEqual(task.stage, "done")
    
    def test_shouldMapInProgressStatusWhenUsingStaticMethodDirectly(self):
        # Given
        original_status = "In Progress"
        
        # When
        status = TaskMetadataPopulator.map_status(self.workflow_config, original_status)
        
        # Then
        self.assertEqual(status, TaskStatus.IN_PROGRESS)
    
    def test_shouldMapDoneStatusWhenUsingStaticMethodDirectly(self):
        # Given
        original_status = "Completed"
        
        # When
        status = TaskMetadataPopulator.map_status(self.workflow_config, original_status)
        
        # Then
        self.assertEqual(status, TaskStatus.DONE)
    
    def test_shouldMapTodoStatusWhenUsingStaticMethodWithUnknownStatus(self):
        # Given
        original_status = "Unknown"
        
        # When
        status = TaskMetadataPopulator.map_status(self.workflow_config, original_status)
        
        # Then
        self.assertEqual(status, TaskStatus.TODO)
    
    def test_shouldResolveDevelopmentStageWhenUsingStaticMethodDirectly(self):
        # Given
        original_status = "Development"
        
        # When
        stage = TaskMetadataPopulator.resolve_stage(self.workflow_config, original_status)
        
        # Then
        self.assertEqual(stage, "development")
    
    def test_shouldResolveQAStageWhenUsingStaticMethodDirectly(self):
        # Given
        original_status = "Testing"
        
        # When
        stage = TaskMetadataPopulator.resolve_stage(self.workflow_config, original_status)
        
        # Then
        self.assertEqual(stage, "qa")
    
    def test_shouldResolveNullStageWhenUsingStaticMethodWithInvalidStatus(self):
        # Given
        original_status = "Invalid"
        
        # When
        stage = TaskMetadataPopulator.resolve_stage(self.workflow_config, original_status)
        
        # Then
        self.assertIsNone(stage)
    
    def test_shouldReturnSameInstanceWhenPopulationCompletes(self):
        # Given
        task = (TaskBuilder.sprint_story()
                .with_original_status("In Progress")
                .build())
        
        # When
        result = self.metadata_convertor.populate_metadata(task)
        
        # Then
        self.assertIs(result, task)
    
    def test_shouldMapComplexEpicToInProgressWithDevelopmentStage(self):
        # Given
        epic = BusinessScenarios.epic_with_child_hierarchy()
        epic.system_metadata.original_status = "In Progress"
        
        # When
        self.metadata_convertor.populate_metadata(epic)
        
        # Then
        self.assertEqual(epic.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(epic.stage, "development")


if __name__ == '__main__':
    unittest.main()