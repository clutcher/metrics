import unittest
from unittest.mock import AsyncMock

from tasks.app.domain.assignee_search_service import AssigneeSearchService
from tasks.app.domain.convertors.task_metadata_convertor import TaskMetadataPopulator
from tasks.app.domain.model.config import TasksConfig, WorkflowConfig
from tasks.app.domain.model.task import TaskSearchCriteria, EnrichmentOptions, WorkTimeExtractorType
from tasks.app.domain.task_search_service import TaskSearchService
from tasks.tests.fixtures.task_builders import BusinessScenarios, TaskBuilder
from tasks.tests.mocks.mock_task_repository import MockTaskRepository


class TestApiTasksCalculation(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.repository = MockTaskRepository()
        self.assignee_search_service = AssigneeSearchService()
        self.config = self._create_test_config()
        self.metadata_convertor = TaskMetadataPopulator(self.config.workflow)
        self.repository_factory_calls = []
        
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
            self.repository_factory_calls.append(worktime_extractor_type)
            return self.repository
        return factory
    
    async def test_shouldUseSimpleWorktimeExtractorWhenNoEnrichmentOptionsSpecified(self):
        # Given
        tasks = BusinessScenarios.sprint_planning_backlog()
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        enrichment = None
        
        # When
        result = await self.task_search_service.search(criteria, enrichment)
        
        # Then
        self.assertEqual([None], self.repository_factory_calls)
    
    async def test_shouldUseSpecificWorktimeExtractorWhenEnrichmentSpecifiesExtractorType(self):
        # Given
        tasks = BusinessScenarios.retrospective_completed_work()
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        enrichment = EnrichmentOptions(
            include_time_tracking=True,
            worktime_extractor_type=WorkTimeExtractorType.BOUNDARY_FROM_RESOLUTION
        )
        
        # When
        result = await self.task_search_service.search(criteria, enrichment)
        
        # Then
        self.assertEqual([WorkTimeExtractorType.BOUNDARY_FROM_RESOLUTION], self.repository_factory_calls)
    
    async def test_shouldUseBoundaryFromLastModifiedExtractorWhenSpecifiedInEnrichment(self):
        # Given
        tasks = BusinessScenarios.capacity_planning_active_work()
        self.repository.mock.find_all.return_value = tasks
        task_ids = ["PROJ-456", "PROJ-654"]
        enrichment = EnrichmentOptions(
            include_time_tracking=True,
            worktime_extractor_type=WorkTimeExtractorType.BOUNDARY_FROM_LAST_MODIFIED
        )
        
        # When
        result = await self.task_search_service.search_by_ids(task_ids, enrichment)
        
        # Then
        self.assertEqual([WorkTimeExtractorType.BOUNDARY_FROM_LAST_MODIFIED], self.repository_factory_calls)
    
    async def test_shouldCalculateTimeTrackingWhenEnrichmentIncludesTimeData(self):
        # Given
        tasks_with_time_tracking = [
            TaskBuilder.retrospective_completed_feature()
                .assigned_to_senior_developer()
                .with_time_spent_hours(20.0)
                .completed()
                .build()
        ]
        self.repository.mock.find_all.return_value = tasks_with_time_tracking
        criteria = TaskSearchCriteria()
        enrichment = EnrichmentOptions(include_time_tracking=True)
        
        # When
        result = await self.task_search_service.search(criteria, enrichment)
        
        # Then
        task = result[0]
        self.assertIsNotNone(task.time_tracking.total_spent_time)
    
    async def test_shouldCalculateWorklogTransitionStatusesWhenEnrichmentSpecifiesStatuses(self):
        # Given
        tasks = BusinessScenarios.sprint_planning_backlog()
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        enrichment = EnrichmentOptions(
            include_time_tracking=True,
            worklog_transition_statuses=["In Progress", "Done", "Testing"]
        )
        
        # When
        result = await self.task_search_service.search(criteria, enrichment)
        
        # Then
        self.repository.mock.find_all.assert_called_once_with(criteria, enrichment)
    
    async def test_shouldCalculateEnrichmentProcessingWhenTasksRequireTimeTrackingData(self):
        # Given
        tasks = BusinessScenarios.retrospective_completed_work()
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        enrichment = EnrichmentOptions(include_time_tracking=True)
        
        # When
        result = await self.task_search_service.search(criteria, enrichment)
        
        # Then
        self.assertEqual(2, len(result))
    
    async def test_shouldCalculateRepositoryFactoryCallsWhenMultipleSearchMethodsUsed(self):
        # Given
        tasks = BusinessScenarios.retrospective_completed_work()
        self.repository.mock.find_all.return_value = tasks
        enrichment_search = EnrichmentOptions(worktime_extractor_type=WorkTimeExtractorType.SIMPLE)
        enrichment_by_ids = EnrichmentOptions(worktime_extractor_type=WorkTimeExtractorType.BOUNDARY_FROM_RESOLUTION)
        
        # When
        await self.task_search_service.search(TaskSearchCriteria(), enrichment_search)
        await self.task_search_service.search_by_ids(["PROJ-789"], enrichment_by_ids)
        
        # Then
        self.assertEqual([WorkTimeExtractorType.SIMPLE, WorkTimeExtractorType.BOUNDARY_FROM_RESOLUTION], self.repository_factory_calls)
    
    async def test_shouldHandleNullEnrichmentCalculationWhenNoOptionsProvided(self):
        # Given
        tasks = BusinessScenarios.sprint_planning_backlog()
        self.repository.mock.find_all.return_value = tasks
        criteria = TaskSearchCriteria()
        enrichment = None
        
        # When
        result = await self.task_search_service.search(criteria, enrichment)
        
        # Then
        self.repository.mock.find_all.assert_called_once_with(criteria, None)


if __name__ == '__main__':
    unittest.main()