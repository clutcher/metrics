from collections import defaultdict
from typing import List, Dict, Union, Optional

from tasks.app.domain.model.config import WorkflowConfig
from ..data.hierarchical_item_data import HierarchicalItemData
from ..data.task_data import TaskData


class TaskGroupingUtils:

    @staticmethod
    def group_ui_tasks_by_member_group_and_stage(
            ui_tasks: List[TaskData],
            workflow_config: WorkflowConfig
    ) -> Union[List[HierarchicalItemData], List[TaskData]]:
        if not ui_tasks:
            return []

        has_meaningful_member_groups = TaskGroupingUtils._has_meaningful_member_groups(ui_tasks)
        has_meaningful_stages = TaskGroupingUtils._has_meaningful_stages(ui_tasks)

        if not has_meaningful_member_groups and not has_meaningful_stages:
            return TaskGroupingUtils._sort_ui_tasks_by_health(ui_tasks)

        if has_meaningful_member_groups and has_meaningful_stages:
            return TaskGroupingUtils._create_member_group_and_stage_groups(ui_tasks, workflow_config)

        if has_meaningful_stages:
            return TaskGroupingUtils._create_stage_groups_only(ui_tasks, workflow_config)

        if has_meaningful_member_groups:
            return TaskGroupingUtils._create_member_group_groups_only(ui_tasks)

        return TaskGroupingUtils._sort_ui_tasks_by_health(ui_tasks)

    @staticmethod
    def _has_meaningful_member_groups(ui_tasks: List[TaskData]) -> bool:
        unique_groups = set()
        for task in ui_tasks:
            member_group = TaskGroupingUtils._extract_member_group_name(task)
            if member_group is not None:
                unique_groups.add(member_group)
        return len(unique_groups) > 1

    @staticmethod
    def _has_meaningful_stages(ui_tasks: List[TaskData]) -> bool:
        unique_stages = set()
        for task in ui_tasks:
            stage = TaskGroupingUtils._extract_stage_name(task)
            if stage is not None:
                unique_stages.add(stage)
        return len(unique_stages) >= 1

    @staticmethod
    def _create_member_group_and_stage_groups(ui_tasks: List[TaskData], workflow_config: WorkflowConfig) -> List[HierarchicalItemData]:
        stage_order = list(workflow_config.stages.keys())
        member_groups = TaskGroupingUtils._group_ui_tasks_by_member_group(ui_tasks)

        grouped_result = []

        for member_group_name in sorted(member_groups.keys()):
            if member_group_name is None:
                continue

            member_group_tasks = member_groups[member_group_name]
            stages_dict = TaskGroupingUtils._group_ui_tasks_by_stage(member_group_tasks)
            stage_groups = TaskGroupingUtils._create_stage_item_groups(stages_dict, stage_order)

            if stage_groups:
                grouped_result.append(HierarchicalItemData(
                    name=member_group_name,
                    type="member_group",
                    count=len(member_group_tasks),
                    items=stage_groups
                ))

        return grouped_result

    @staticmethod
    def _create_stage_groups_only(ui_tasks: List[TaskData], workflow_config: WorkflowConfig) -> List[HierarchicalItemData]:
        stage_order = list(workflow_config.stages.keys())
        stages_dict = TaskGroupingUtils._group_ui_tasks_by_stage(ui_tasks)
        return TaskGroupingUtils._create_stage_item_groups(stages_dict, stage_order)

    @staticmethod
    def _create_member_group_groups_only(ui_tasks: List[TaskData]) -> List[HierarchicalItemData]:
        member_groups = TaskGroupingUtils._group_ui_tasks_by_member_group(ui_tasks)

        grouped_result = []

        for member_group_name in sorted(member_groups.keys()):
            if member_group_name is None:
                continue

            member_group_tasks = member_groups[member_group_name]
            sorted_tasks = TaskGroupingUtils._sort_ui_tasks_by_health(member_group_tasks)

            grouped_result.append(HierarchicalItemData(
                name=member_group_name,
                type="member_group",
                count=len(sorted_tasks),
                items=sorted_tasks
            ))

        return grouped_result

    @staticmethod
    def _group_ui_tasks_by_member_group(ui_tasks: List[TaskData]) -> Dict[Optional[str], List[TaskData]]:
        member_groups = defaultdict(list)
        for task in ui_tasks:
            member_groups[TaskGroupingUtils._extract_member_group_name(task)].append(task)
        return member_groups

    @staticmethod
    def _group_ui_tasks_by_stage(ui_tasks: List[TaskData]) -> Dict[Optional[str], List[TaskData]]:
        stages_dict = defaultdict(list)
        for task in ui_tasks:
            stages_dict[TaskGroupingUtils._extract_stage_name(task)].append(task)
        return stages_dict

    @staticmethod
    def _create_stage_item_groups(stages_dict: Dict[Optional[str], List[TaskData]], stage_order: List[str]) -> List[HierarchicalItemData]:
        stage_groups = []
        valid_stages = {k: v for k, v in stages_dict.items() if k is not None}

        sorted_stage_names = sorted(
            valid_stages.keys(),
            key=lambda stage_name: TaskGroupingUtils._calculate_stage_sort_key(stage_name, stage_order)
        )

        for stage_name in sorted_stage_names:
            stage_tasks = valid_stages[stage_name]
            sorted_tasks = TaskGroupingUtils._sort_ui_tasks_by_health(stage_tasks)

            stage_groups.append(HierarchicalItemData(
                name=stage_name,
                type="stage",
                count=len(sorted_tasks),
                items=sorted_tasks
            ))

        return stage_groups

    @staticmethod
    def _sort_ui_tasks_by_health(ui_tasks: List[TaskData]) -> List[TaskData]:
        sorted_tasks = ui_tasks.copy()
        sorted_tasks.sort(key=TaskGroupingUtils._extract_health_status_value, reverse=True)
        return sorted_tasks

    @staticmethod
    def _extract_member_group_name(ui_task: TaskData) -> Optional[str]:
        if ui_task.assignment and ui_task.assignment.member_group:
            return ui_task.assignment.member_group.name
        return None

    @staticmethod
    def _extract_stage_name(ui_task: TaskData) -> Optional[str]:
        return ui_task.stage

    @staticmethod
    def _extract_health_status_value(ui_task: TaskData) -> int:
        if ui_task.forecast and ui_task.forecast.health_status:
            return ui_task.forecast.health_status.value
        return 0

    @staticmethod
    def _calculate_stage_sort_key(stage_name: str, stage_order: List[str]) -> tuple[int, str]:
        return (stage_order.index(stage_name) if stage_name in stage_order else len(stage_order), stage_name)
