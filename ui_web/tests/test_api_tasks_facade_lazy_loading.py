import unittest
from unittest.mock import Mock

from sd_metrics_lib.utils.enums import HealthStatus
from sd_metrics_lib.utils.time import Duration, TimeUnit, TimePolicy

from forecast.app.domain.model.forecast import Forecast, Target, Subject
from tasks.app.domain.model.config import WorkflowConfig
from tasks.app.domain.model.task import TaskSearchCriteria, MemberGroup
from ui_web.convertors.member_convertor import MemberConvertor
from ui_web.convertors.task_convertor import TaskConvertor
from ui_web.facades.tasks_facade import TasksFacade
from ui_web.tests.fixtures.ui_web_builders import DomainTaskBuilder
from ui_web.tests.mocks.mock_forecast_api import MockForecastApi
from ui_web.tests.mocks.mock_task_search_api import MockTaskSearchApi
from ui_web.utils.federated_data_post_processors import MemberGroupTaskFilter


class TestTasksFacadeLazyLoading(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.task_search_api = MockTaskSearchApi()
        self.forecast_api = MockForecastApi()

        self.workflow_config = WorkflowConfig(
            in_progress_status_codes=["In Progress", "Development", "Testing"],
            done_status_codes=["Done", "Completed", "Closed"],
            pending_status_codes=["To Do", "Open", "Backlog"],
            stages={"development": ["In Progress", "Development"], "done": ["Done"]},
            recently_finished_tasks_days=30
        )

        member_group_config = Mock()
        member_group_config.members = {"alice.johnson": {"member_groups": ["frontend-team"]}}
        member_group_config.default_member_group_when_missing = None
        member_group_config.custom_filters = {}

        self.facade = TasksFacade(
            task_search_api=self.task_search_api,
            forecast_api=self.forecast_api,
            task_convertor=TaskConvertor(TimePolicy.BUSINESS_HOURS),
            available_member_groups=[MemberGroup(id="frontend-team", name="Frontend Team")],
            current_tasks_search_criteria=TaskSearchCriteria(status_filter=["In Progress"]),
            recently_finished_tasks_search_criteria=TaskSearchCriteria(status_filter=["Done"]),
            workflow_config=self.workflow_config,
            member_group_task_filter=MemberGroupTaskFilter(member_group_config),
            member_convertor=MemberConvertor()
        )

    def _make_task(self, task_id: str):
        return (DomainTaskBuilder(task_id, f"Implement feature {task_id}")
                .assigned_to("alice.johnson")
                .with_story_points(5.0)
                .with_stage("development")
                .build())

    def _apply_red_health_forecast(self, tasks, parameters):
        for task in tasks:
            task.forecast = Forecast(
                velocity=1.0,
                estimation_time=Duration.of(1.0, TimeUnit.DAY),
                target=Target(id=task.id, health_status=HealthStatus.RED),
                subject=Subject()
            )
        return tasks

    async def test_shouldLeaveStructuralTasksWithoutHealthWhenFetchingStructure(self):
        # given
        self.task_search_api.mock.search.side_effect = [[self._make_task("1")], []]
        self.forecast_api.mock.generate_forecasts_for_tasks.side_effect = self._apply_red_health_forecast

        # when
        result = await self.facade.get_task_structure()

        # then
        self.assertIsNone(result[0].forecast)

    async def test_shouldEnrichStageTasksWithHealthWhenFetchedByIds(self):
        # given
        self.task_search_api.mock.search.return_value = [self._make_task("1")]
        self.forecast_api.mock.generate_forecasts_for_tasks.side_effect = self._apply_red_health_forecast

        # when
        result = await self.facade.get_tasks_by_ids(["1"])

        # then
        self.assertEqual(HealthStatus.RED, result[0].forecast.health_status)

    async def test_shouldReturnExactlyTheRequestedStageTasksWhenFetchingByIds(self):
        # given
        available_tasks = {task_id: self._make_task(task_id) for task_id in ["1", "2", "3"]}

        async def return_requested_tasks(criteria, enrichment):
            return [available_tasks[task_id] for task_id in criteria.id_filter]

        self.task_search_api.mock.search.side_effect = return_requested_tasks

        # when
        result = await self.facade.get_tasks_by_ids(["1", "2"])

        # then
        self.assertEqual(["1", "2"], [task.id for task in result])

    async def test_shouldReturnNoTasksWithoutSearchingWhenNoTaskIdsGiven(self):
        # given
        # when
        result = await self.facade.get_tasks_by_ids([])

        # then
        self.assertEqual([], result)
        self.task_search_api.mock.search.assert_not_called()
