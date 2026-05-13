import unittest
from unittest.mock import MagicMock

from tasks.app.domain.model.config import (
    TasksConfig, JiraConfig, AzureConfig, ProjectConfig, WorkflowConfig,
    TaskFilterConfig, MemberGroupConfig, EstimationConfig, SortingConfig
)
from tasks.out.convertors.jira import JiraTaskConverter


def _build_tasks_config(jira_release_field: str = None) -> TasksConfig:
    return TasksConfig(
        jira=JiraConfig(
            jira_server_url="https://example.atlassian.net",
            jira_email="test@example.com",
            jira_api_token="token",
            story_point_custom_field_id="customfield_10016",
            release_field=jira_release_field
        ),
        azure=AzureConfig(azure_organization_url=None, azure_pat=None),
        project=ProjectConfig(project_keys=["PROJ"], task_tracker="jira"),
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


def _build_jira_response(extra_fields: dict = None) -> dict:
    fields = {
        "summary": "Implement release dashboard",
        "status": {"name": "In Progress"},
        "priority": {"id": "3"}
    }
    if extra_fields:
        fields.update(extra_fields)
    return {"key": "PROJ-101", "fields": fields}


def _build_converter(config: TasksConfig) -> JiraTaskConverter:
    worklog_extractor = MagicMock()
    worklog_extractor.get_work_time_per_user.return_value = {}
    story_point_extractor = MagicMock()
    story_point_extractor.get_story_points.return_value = None
    return JiraTaskConverter(config, worklog_extractor, story_point_extractor)


class TestJiraTaskConverterRelease(unittest.TestCase):

    def test_shouldExtractReleasesFromConfiguredFieldWhenJiraReturnsFixVersionsList(self):
        # given
        config = _build_tasks_config(jira_release_field="fixVersions")
        converter = _build_converter(config)
        jira_response = _build_jira_response({
            "fixVersions": [
                {"id": "10001", "name": "Release 2026.015"},
                {"id": "10002", "name": "Release 2026.016"}
            ]
        })

        # when
        task = converter.convert_to_task(jira_response)

        # then
        self.assertEqual(2, len(task.releases))
        self.assertEqual("Release 2026.015", task.releases[0].name)
        self.assertEqual("10001", task.releases[0].id)
        self.assertEqual("Release 2026.016", task.releases[1].name)

    def test_shouldExtractReleaseWhenJiraFieldReturnsSingleString(self):
        # given
        config = _build_tasks_config(jira_release_field="customfield_99999")
        converter = _build_converter(config)
        jira_response = _build_jira_response({"customfield_99999": "v2.3.0"})

        # when
        task = converter.convert_to_task(jira_response)

        # then
        self.assertEqual(1, len(task.releases))
        self.assertEqual("v2.3.0", task.releases[0].name)

    def test_shouldSplitCommaSeparatedReleaseStringAndTrimWhitespace(self):
        # given
        config = _build_tasks_config(jira_release_field="customfield_99999")
        converter = _build_converter(config)
        jira_response = _build_jira_response({"customfield_99999": "2026.015, 2026.016 ,  2026.017"})

        # when
        task = converter.convert_to_task(jira_response)

        # then
        self.assertEqual(["2026.015", "2026.016", "2026.017"], [release.name for release in task.releases])

    def test_shouldLeaveReleasesUnsetWhenReleaseFieldIsNotConfigured(self):
        # given
        config = _build_tasks_config(jira_release_field=None)
        converter = _build_converter(config)
        jira_response = _build_jira_response({
            "fixVersions": [{"id": "10001", "name": "Release 2026.015"}]
        })

        # when
        task = converter.convert_to_task(jira_response)

        # then
        self.assertIsNone(task.releases)

    def test_shouldLeaveReleasesUnsetWhenJiraResponseIsMissingField(self):
        # given
        config = _build_tasks_config(jira_release_field="fixVersions")
        converter = _build_converter(config)
        jira_response = _build_jira_response()

        # when
        task = converter.convert_to_task(jira_response)

        # then
        self.assertIsNone(task.releases)
