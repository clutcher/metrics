from typing import List, Optional, Callable, Dict, Any
from unittest.mock import AsyncMock

from tasks.app.domain.model.task import TaskSearchCriteria, Task, EnrichmentOptions
from tasks.app.spi.task_repository import TaskRepository


class MockTaskRepository(TaskRepository):
    """
    Mock repository that supports both testing scenarios:
    - Scenario A (Jira-style): Returns complete hierarchies in first request
    - Scenario B (Azure-style): Returns only direct children, requiring incremental loading
    """
    
    def __init__(self):
        self._mock = AsyncMock()
        self._call_log: List[TaskSearchCriteria] = []
        
    async def find_all(self,
                       search_criteria: Optional[TaskSearchCriteria] = None,
                       enrichment: Optional[EnrichmentOptions] = None
                       ) -> List[Task]:
        if search_criteria:
            self._call_log.append(search_criteria)
        return await self._mock.find_all(search_criteria, enrichment)
    
    @property
    def mock(self) -> AsyncMock:
        return self._mock
    
    @property
    def call_log(self) -> List[TaskSearchCriteria]:
        """Returns log of all search criteria used in calls to find_all"""
        return self._call_log.copy()
    
    def setup_jira_style_behavior(self, complete_hierarchies: List[Task]):
        """
        Setup Scenario A: Jira-style behavior where complete hierarchies are returned
        in the first request, simulating repository that loads full task trees.
        """
        self._mock.find_all.return_value = complete_hierarchies
    
    def setup_azure_style_behavior(self, incremental_loader: Callable[[Optional[TaskSearchCriteria]], List[Task]]):
        """
        Setup Scenario B: Azure-style behavior where only direct children are returned
        per request, requiring multiple calls to build complete hierarchies.
        
        Args:
            incremental_loader: Function that takes TaskSearchCriteria and returns 
                               tasks with only their direct children loaded
        """
        self._mock.find_all.side_effect = lambda criteria, enrichment=None: incremental_loader(criteria)
    
    def reset_call_log(self):
        """Reset the call log for fresh test tracking"""
        self._call_log.clear()
    
    def get_requested_task_ids_by_call(self) -> List[List[str]]:
        """
        Returns list of task ID filters for each repository call.
        Useful for asserting on batched loading behavior.
        """
        return [
            criteria.id_filter if criteria and criteria.id_filter else []
            for criteria in self._call_log
        ]
    
    def assert_minimum_calls(self, min_calls: int, message: str = ""):
        """Assert minimum number of repository calls made"""
        actual_calls = len(self._call_log)
        if actual_calls < min_calls:
            raise AssertionError(f"Expected at least {min_calls} repository calls, got {actual_calls}. {message}")
    
    def assert_maximum_calls(self, max_calls: int, message: str = ""):
        """Assert maximum number of repository calls made"""
        actual_calls = len(self._call_log)
        if actual_calls > max_calls:
            raise AssertionError(f"Expected at most {max_calls} repository calls, got {actual_calls}. {message}")
    
    def assert_batched_loading_used(self, message: str = ""):
        """Assert that at least one call requested multiple task IDs (batched loading)"""
        batched_calls = [
            call for call in self._call_log 
            if call and call.id_filter and len(call.id_filter) > 1
        ]
        if not batched_calls:
            raise AssertionError(f"Expected at least one batched loading call (multiple task IDs), but all calls were single-task. {message}")
    
    def get_call_summary(self) -> Dict[str, Any]:
        """Get summary of repository call patterns for debugging"""
        return {
            "total_calls": len(self._call_log),
            "calls_with_id_filter": len([c for c in self._call_log if c and c.id_filter]),
            "batched_calls": len([c for c in self._call_log if c and c.id_filter and len(c.id_filter) > 1]),
            "unique_task_ids_requested": len(set().union(*[
                c.id_filter for c in self._call_log 
                if c and c.id_filter
            ])) if any(c and c.id_filter for c in self._call_log) else 0
        }