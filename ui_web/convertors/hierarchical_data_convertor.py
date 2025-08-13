from typing import List, Union

from tasks.app.domain.model.config import WorkflowConfig
from ..convertors.task_convertor import TaskConvertor
from ..data.hierarchical_item_data import HierarchicalItemData
from ..data.task_data import TaskData
from ..utils.task_grouping_utils import TaskGroupingUtils


class HierarchicalItemConvertor:

    def __init__(self, task_convertor: TaskConvertor):
        self.task_convertor = task_convertor

    def convert_tasks_to_hierarchical_data(
            self,
            ui_tasks: List[TaskData],
            workflow_config: WorkflowConfig
    ) -> Union[List[HierarchicalItemData], List[TaskData]]:
        hierarchical_groups = TaskGroupingUtils.group_ui_tasks_by_member_group_and_stage(ui_tasks, workflow_config)

        if isinstance(hierarchical_groups, list) and len(hierarchical_groups) > 0 and isinstance(hierarchical_groups[0],
                                                                                                 HierarchicalItemData):
            result = [self._convert_hierarchical_item_tasks(group) for group in hierarchical_groups]
            return result

        return hierarchical_groups

    def _convert_hierarchical_item_tasks(self, hierarchical_item: HierarchicalItemData) -> HierarchicalItemData:
        converted_items = []

        for item in hierarchical_item.items:
            if isinstance(item, HierarchicalItemData):
                converted_items.append(self._convert_hierarchical_item_tasks(item))
            else:
                if self.task_convertor:
                    converted_items.append(self.task_convertor.convert_task_to_data(item))
                else:
                    converted_items.append(item)

        return HierarchicalItemData(
            name=hierarchical_item.name,
            type=hierarchical_item.type,
            count=hierarchical_item.count,
            items=converted_items
        )
