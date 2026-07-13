import unittest
from unittest.mock import MagicMock

from tasks.app.domain.model.config import (
    TasksConfig, JiraConfig, AzureConfig, ProjectConfig, WorkflowConfig,
    TaskFilterConfig, MemberGroupConfig, EstimationConfig, SortingConfig
)
from tasks.out.convertors.azure import AzureTaskConverter


def _build_tasks_config(azure_iteration_field: str = None, azure_release_field: str = None) -> TasksConfig:
    return TasksConfig(
        jira=JiraConfig(jira_server_url=None, jira_email=None, jira_api_token=None, story_point_custom_field_id=""),
        azure=AzureConfig(
            azure_organization_url="https://dev.azure.com/example",
            azure_pat="pat",
            release_field=azure_release_field,
            iteration_field=azure_iteration_field
        ),
        project=ProjectConfig(project_keys=["Empower"], task_tracker="azure"),
        workflow=WorkflowConfig(
            stages={"Development": ["In Progress"]},
            in_progress_status_codes=["In Progress"],
            pending_status_codes=["Blocked"],
            done_status_codes=["Done"],
            recently_finished_tasks_days=14
        ),
        task_filter=TaskFilterConfig(global_task_types_filter=None, global_team_filter=None),
        member_group=MemberGroupConfig(members={}, default_member_group_when_missing=None),
        estimation=EstimationConfig(
            working_days_per_month=22,
            default_story_points_value_when_missing=3.0,
            ideal_hours_per_day=4.0,
            story_points_to_ideal_hours_convertion_ratio=1.0,
            default_seniority_level_when_missing="middle",
            default_health_status_when_missing="GREEN"
        ),
        sorting=SortingConfig(stage_sort_overrides={}, default_sort_criteria="-health")
    )


def _build_azure_work_item(extra_fields: dict = None):
    fields = {
        "System.Title": "Implement iteration filter",
        "System.State": "In Progress",
        "System.TeamProject": "Empower"
    }
    if extra_fields:
        fields.update(extra_fields)
    work_item = MagicMock()
    work_item.id = 54321
    work_item.fields = fields
    return work_item


def _build_converter(config: TasksConfig) -> AzureTaskConverter:
    worklog_extractor = MagicMock()
    worklog_extractor.get_work_time_per_user.return_value = {}
    story_point_extractor = MagicMock()
    story_point_extractor.get_story_points.return_value = None
    return AzureTaskConverter(config, worklog_extractor, story_point_extractor)


class TestAzureTaskConverterIteration(unittest.TestCase):

    def test_shouldExtractLeafSegmentFromIterationPath(self):
        # given
        config = _build_tasks_config(azure_iteration_field="System.IterationPath")
        converter = _build_converter(config)
        work_item = _build_azure_work_item({"System.IterationPath": "Empower\\Release 2024\\Sprint 12"})

        # when
        task = converter.convert_to_task(work_item)

        # then
        self.assertEqual("Sprint 12", task.iteration)

    def test_shouldExtractIterationVerbatimWhenCustomFieldHoldsPlainString(self):
        # given
        config = _build_tasks_config(azure_iteration_field="Custom.Iteration")
        converter = _build_converter(config)
        work_item = _build_azure_work_item({"Custom.Iteration": "Sprint 5"})

        # when
        task = converter.convert_to_task(work_item)

        # then
        self.assertEqual("Sprint 5", task.iteration)

    def test_shouldLeaveIterationUnsetWhenIterationFieldIsNotConfigured(self):
        # given
        config = _build_tasks_config(azure_iteration_field=None)
        converter = _build_converter(config)
        work_item = _build_azure_work_item({"System.IterationPath": "Empower\\Sprint 12"})

        # when
        task = converter.convert_to_task(work_item)

        # then
        self.assertIsNone(task.iteration)

    def test_shouldLeaveIterationUnsetWhenWorkItemIsMissingField(self):
        # given
        config = _build_tasks_config(azure_iteration_field="System.IterationPath")
        converter = _build_converter(config)
        work_item = _build_azure_work_item()

        # when
        task = converter.convert_to_task(work_item)

        # then
        self.assertIsNone(task.iteration)

    def test_shouldPopulateReleaseAndIterationIndependentlyWhenBothFieldsAreConfigured(self):
        # given
        config = _build_tasks_config(azure_iteration_field="System.IterationPath", azure_release_field="Custom.Release")
        converter = _build_converter(config)
        work_item = _build_azure_work_item({
            "Custom.Release": "2026.015",
            "System.IterationPath": "Empower\\Release 2024\\Sprint 12"
        })

        # when
        task = converter.convert_to_task(work_item)

        # then
        self.assertEqual("2026.015", task.releases[0].name)
        self.assertEqual("Sprint 12", task.iteration)


if __name__ == '__main__':
    unittest.main()
