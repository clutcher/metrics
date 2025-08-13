from typing import Optional
from unittest.mock import Mock

from tasks.app.api.api_for_assignee_search import ApiForAssigneeSearch
from tasks.app.domain.model.task import Assignee


class MockAssigneeSearchApi(ApiForAssigneeSearch):
    
    def __init__(self):
        self._mock = Mock()
        
    def get_assignee_by_id(self, assignee_id: str) -> Optional[Assignee]:
        return self._mock.get_assignee_by_id(assignee_id)
    
    @property
    def mock(self) -> Mock:
        return self._mock