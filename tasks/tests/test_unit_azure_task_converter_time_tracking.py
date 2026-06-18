import unittest
from unittest.mock import MagicMock

from sd_metrics_lib.utils.time import Duration, TimeUnit

from tasks.app.domain.model.config import (
    TasksConfig, JiraConfig, AzureConfig, ProjectConfig, WorkflowConfig,
    TaskFilterConfig, MemberGroupConfig, EstimationConfig, SortingConfig
)
from tasks.out.convertors.azure import AzureTaskConverter


def _build_tasks_config() -> TasksConfig:
    return TasksConfig(
        jira=JiraConfig(jira_server_url=None, jira_email=None, jira_api_token=None, story_point_custom_field_id=""),
        azure=AzureConfig(azure_organization_url="https://dev.azure.com/example", azure_pat="pat", release_field=None),
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


def _build_azure_work_item():
    work_item = MagicMock()
    work_item.id = 12345
    work_item.fields = {"System.Title": "Build dashboard", "System.State": "In Progress", "System.TeamProject": "Empower"}
    return work_item


def _build_worklog_extractor():
    worklog_extractor = MagicMock()
    worklog_extractor.get_work_time_per_user.return_value = {"alice": Duration.of(8.0, TimeUnit.HOUR)}
    return worklog_extractor


def _build_story_point_extractor():
    story_point_extractor = MagicMock()
    story_point_extractor.get_story_points.return_value = None
    return story_point_extractor


class TestAzureTaskConverterTimeTracking(unittest.TestCase):

    def test_shouldSkipChangelogWorklogExtractionWhenTimeTrackingIsDisabled(self):
        # given
        worklog_extractor = _build_worklog_extractor()
        converter = AzureTaskConverter(_build_tasks_config(), worklog_extractor, _build_story_point_extractor(),
                                       include_time_tracking=False)
        work_item = _build_azure_work_item()

        # when
        converter.convert_to_task(work_item)

        # then
        worklog_extractor.get_work_time_per_user.assert_not_called()

    def test_shouldLeaveSpentTimeAtZeroWhenTimeTrackingIsDisabled(self):
        # given
        converter = AzureTaskConverter(_build_tasks_config(), _build_worklog_extractor(), _build_story_point_extractor(),
                                       include_time_tracking=False)
        work_item = _build_azure_work_item()

        # when
        task = converter.convert_to_task(work_item)

        # then
        self.assertEqual(Duration.zero(), task.time_tracking.total_spent_time)

    def test_shouldExtractSpentTimeFromChangelogWhenTimeTrackingIsEnabled(self):
        # given
        converter = AzureTaskConverter(_build_tasks_config(), _build_worklog_extractor(), _build_story_point_extractor(),
                                       include_time_tracking=True)
        work_item = _build_azure_work_item()

        # when
        task = converter.convert_to_task(work_item)

        # then
        self.assertEqual(Duration.of(8.0, TimeUnit.HOUR), task.time_tracking.total_spent_time)
