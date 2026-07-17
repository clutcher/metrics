import unittest

from tasks.app.domain.model.config import WorkflowConfig, SortingConfig
from ui_web.data.task_data import TaskData, AssignmentData, AssigneeData, TimeTrackingData, SystemMetadataData
from ui_web.utils.task_grouping_utils import TaskGroupingUtils


class TestTaskGroupingUtilsGroupByAllStageColumns(unittest.TestCase):

    def test_shouldIncludeEveryConfiguredStageAsColumnEvenWhenEmpty(self):
        # Given
        tasks = [_build_task("TASK-1", stage="Development")]
        workflow_config = _build_workflow_config(["Analysis", "Development", "Validation"])

        # When
        result = TaskGroupingUtils.group_tasks_by_all_stage_columns(tasks, workflow_config)

        # Then
        column_names = [column.name for column in result]
        self.assertEqual(["Analysis", "Development", "Validation"], column_names)
        self.assertEqual(0, result[0].count)
        self.assertEqual(1, result[1].count)
        self.assertEqual(0, result[2].count)

    def test_shouldOrderColumnsAccordingToWorkflowConfigStageOrder(self):
        # Given
        tasks = [
            _build_task("TASK-1", stage="Validation"),
            _build_task("TASK-2", stage="Analysis"),
        ]
        workflow_config = _build_workflow_config(["Analysis", "Development", "Validation"])

        # When
        result = TaskGroupingUtils.group_tasks_by_all_stage_columns(tasks, workflow_config)

        # Then
        self.assertEqual(["Analysis", "Development", "Validation"], [column.name for column in result])

    def test_shouldExcludeTasksWithNoResolvedStage(self):
        # Given
        tasks = [_build_task("TASK-1", stage=None)]
        workflow_config = _build_workflow_config(["Analysis", "Development"])

        # When
        result = TaskGroupingUtils.group_tasks_by_all_stage_columns(tasks, workflow_config)

        # Then
        total_tasks_in_columns = sum(column.count for column in result)
        self.assertEqual(0, total_tasks_in_columns)

    def test_shouldSortTasksWithinEachColumnUsingSortingConfig(self):
        # Given
        tasks = [
            _build_task("TASK-1", stage="Development", priority=2),
            _build_task("TASK-2", stage="Development", priority=1),
        ]
        workflow_config = _build_workflow_config(["Development"])
        sorting_config = SortingConfig(default_sort_criteria="priority", stage_sort_overrides={})

        # When
        result = TaskGroupingUtils.group_tasks_by_all_stage_columns(tasks, workflow_config, sorting_config)

        # Then
        development_column = result[0]
        self.assertEqual(["TASK-2", "TASK-1"], [task.id for task in development_column.items])


class TestTaskGroupingUtilsGroupByKey(unittest.TestCase):

    def test_shouldGroupTasksByExtractedKeyAndSortAlphabetically(self):
        # Given
        tasks = [
            _build_task("TASK-1", assignee_id="charlie"),
            _build_task("TASK-2", assignee_id="alice"),
            _build_task("TASK-3", assignee_id="alice"),
            _build_task("TASK-4", assignee_id="bob"),
        ]

        # When
        result = TaskGroupingUtils.group_tasks_by_key(
            tasks, key_extractor=lambda t: t.assignment.assignee.id, group_type="developer"
        )

        # Then
        self.assertEqual(3, len(result))
        self.assertEqual("alice", result[0].name)
        self.assertEqual(2, result[0].count)
        self.assertEqual("bob", result[1].name)
        self.assertEqual(1, result[1].count)
        self.assertEqual("charlie", result[2].name)
        self.assertEqual(1, result[2].count)

    def test_shouldExcludeTasksWhereKeyExtractorReturnsNone(self):
        # Given
        tasks = [
            _build_task("TASK-1", assignee_id="alice"),
            _build_task("TASK-2", assignee_id=None),
            _build_task("TASK-3", assignee_id="bob"),
        ]

        # When
        result = TaskGroupingUtils.group_tasks_by_key(
            tasks,
            key_extractor=lambda t: t.assignment.assignee.id if t.assignment.assignee else None,
            group_type="developer"
        )

        # Then
        self.assertEqual(2, len(result))
        group_names = [g.name for g in result]
        self.assertNotIn(None, group_names)

    def test_shouldSetCorrectGroupTypeOnAllGroups(self):
        # Given
        tasks = [
            _build_task("TASK-1", assignee_id="alice"),
            _build_task("TASK-2", assignee_id="bob"),
        ]

        # When
        result = TaskGroupingUtils.group_tasks_by_key(
            tasks, key_extractor=lambda t: t.assignment.assignee.id, group_type="developer"
        )

        # Then
        for group in result:
            self.assertEqual("developer", group.type)


def _build_task(task_id, assignee_id=None, stage=None, priority=None):
    assignee = AssigneeData(id=assignee_id, display_name=assignee_id or "") if assignee_id else None
    return TaskData(
        id=task_id,
        title=f"Task {task_id}",
        assignment=AssignmentData(assignee=assignee),
        time_tracking=TimeTrackingData(),
        system_metadata=SystemMetadataData(original_status="To Do"),
        stage=stage,
        priority=priority
    )


def _build_workflow_config(stage_names):
    return WorkflowConfig(
        stages={stage_name: [] for stage_name in stage_names},
        in_progress_status_codes=[],
        pending_status_codes=[],
        done_status_codes=[],
        recently_finished_tasks_days=14
    )
