from abc import ABC, abstractmethod
from typing import Optional

from ..domain.model.task import Assignee


class ApiForAssigneeSearch(ABC):

    @abstractmethod
    def get_assignee_by_id(self, assignee_id: str) -> Optional[Assignee]:
        pass