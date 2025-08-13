from typing import Optional, List

from ..model.config import WorkflowConfig
from ..model.task import Task, TaskStatus


class TaskMetadataPopulator:

    def __init__(self, workflow_config: WorkflowConfig):
        self._workflow_config = workflow_config

    def populate_metadata_for_tasks(self, tasks: List[Task]) -> List[Task]:
        for task in tasks:
            self.populate_metadata(task)
        return tasks

    def populate_metadata(self, task: Task) -> Task:
        original_status = task.system_metadata.original_status
        task.status = TaskMetadataPopulator.map_status(self._workflow_config, original_status)
        task.stage = TaskMetadataPopulator.resolve_stage(self._workflow_config, original_status)
        return task

    @staticmethod
    def resolve_stage(workflow: WorkflowConfig, original_status: Optional[str]) -> Optional[str]:
        if not original_status:
            return None

        for stage_name, statuses in workflow.stages.items():
            if original_status in statuses:
                return stage_name
        return None

    @staticmethod
    def map_status(workflow: WorkflowConfig, original_status: Optional[str]) -> TaskStatus:
        if not original_status:
            return TaskStatus.TODO

        if workflow.done_status_codes and original_status in workflow.done_status_codes:
            return TaskStatus.DONE

        if workflow.in_progress_status_codes and original_status in workflow.in_progress_status_codes:
            return TaskStatus.IN_PROGRESS

        return TaskStatus.TODO
