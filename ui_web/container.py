from sd_metrics_lib.utils.time import TimePolicy

from forecast.container import forecast_container
from tasks.container import tasks_container
from velocity.container import velocity_container
from .convertors.member_convertor import MemberConvertor
from .convertors.task_convertor import TaskConvertor
from .convertors.task_forecast_chart_convertor import TaskForecastChartConvertor
from .convertors.task_forecast_convertor import TaskForecastConvertor
from .convertors.velocity_chart_convertor import VelocityChartConvertor
from .convertors.velocity_report_convertor import VelocityReportConvertor
from .facades.child_tasks_facade import ChildTasksFacade
from .facades.dev_velocity_facade import DevVelocityFacade
from .facades.members_facade import MembersFacade
from .facades.task_forecast_facade import TaskForecastFacade
from .facades.tasks_facade import TasksFacade
from .facades.team_velocity_facade import TeamVelocityFacade
from .utils.federated_data_post_processors import MemberGroupTaskFilter


class UiWebContainer:
    def __init__(self):
        self._task_convertor = None
        self._forecast_task_convertor = None
        self._member_convertor = None
        self._task_forecast_convertor = None
        self._velocity_chart_convertor = None
        self._velocity_report_convertor = None
        self._task_forecast_chart_convertor = None

        self._tasks_facade = None
        self._child_tasks_facade = None
        self._members_facade = None
        self._team_velocity_facade = None
        self._dev_velocity_facade = None
        self._task_forecast_facade = None
        self._member_group_task_filter = None

    @property
    def task_convertor(self) -> TaskConvertor:
        if self._task_convertor is None:
            self._task_convertor = TaskConvertor(velocity_container.ideal_time_policy)
        return self._task_convertor

    @property
    def forecast_task_convertor(self) -> TaskConvertor:
        if self._forecast_task_convertor is None:
            self._forecast_task_convertor = TaskConvertor(TimePolicy.BUSINESS_HOURS)
        return self._forecast_task_convertor

    @property
    def member_convertor(self) -> MemberConvertor:
        if self._member_convertor is None:
            self._member_convertor = MemberConvertor()
        return self._member_convertor


    @property
    def task_forecast_convertor(self) -> TaskForecastConvertor:
        if self._task_forecast_convertor is None:
            self._task_forecast_convertor = TaskForecastConvertor()
        return self._task_forecast_convertor

    @property
    def tasks_facade(self) -> TasksFacade:
        if self._tasks_facade is None:
            self._tasks_facade = TasksFacade(
                task_search_api=tasks_container.task_search_api,
                forecast_api=forecast_container.forecast_api,
                task_convertor=self.task_convertor,
                available_member_groups=tasks_container.get_available_member_groups(),
                current_tasks_search_criteria=tasks_container.create_current_tasks_search_criteria(),
                recently_finished_tasks_search_criteria=tasks_container.create_recently_finished_tasks_search_criteria(),
                workflow_config=tasks_container.get_workflow_config(),
                member_group_task_filter=self._get_member_group_task_filter(),
                member_convertor=self.member_convertor
            )
        return self._tasks_facade

    @property
    def child_tasks_facade(self) -> ChildTasksFacade:
        if self._child_tasks_facade is None:
            self._child_tasks_facade = ChildTasksFacade(
                tasks_container.task_search_api,
                forecast_container.forecast_api,
                self.task_convertor
            )
        return self._child_tasks_facade

    @property
    def members_facade(self) -> MembersFacade:
        if self._members_facade is None:
            self._members_facade = MembersFacade(
                tasks_container.task_search_api,
                self.member_convertor
            )
        return self._members_facade

    @property
    def team_velocity_facade(self) -> TeamVelocityFacade:
        if self._team_velocity_facade is None:
            self._team_velocity_facade = TeamVelocityFacade(
                velocity_container.velocity_report_generation_api,
                tasks_container.assignee_search_api,
                tasks_container.get_available_member_groups(),
                self.member_convertor,
                self._get_velocity_chart_convertor(),
                self._get_velocity_report_convertor()
            )
        return self._team_velocity_facade

    @property
    def dev_velocity_facade(self) -> DevVelocityFacade:
        if self._dev_velocity_facade is None:
            self._dev_velocity_facade = DevVelocityFacade(
                velocity_container.velocity_report_generation_api,
                tasks_container.assignee_search_api,
                tasks_container.get_available_member_groups(),
                tasks_container.create_velocity_search_criteria,
                self.member_convertor,
                self._get_velocity_chart_convertor(),
                self._get_velocity_report_convertor()
            )
        return self._dev_velocity_facade

    @property
    def task_forecast_facade(self) -> TaskForecastFacade:
        if self._task_forecast_facade is None:
            self._task_forecast_facade = TaskForecastFacade(
                forecast_container.forecast_api,
                self.task_forecast_convertor,
                self.forecast_task_convertor,
                self._get_task_forecast_chart_convertor()
            )
        return self._task_forecast_facade

    def _get_member_group_task_filter(self) -> MemberGroupTaskFilter:
        if self._member_group_task_filter is None:
            self._member_group_task_filter = MemberGroupTaskFilter(tasks_container.get_member_group_config())
        return self._member_group_task_filter

    def _get_velocity_chart_convertor(self) -> VelocityChartConvertor:
        if self._velocity_chart_convertor is None:
            self._velocity_chart_convertor = VelocityChartConvertor()
        return self._velocity_chart_convertor

    def _get_velocity_report_convertor(self) -> VelocityReportConvertor:
        if self._velocity_report_convertor is None:
            self._velocity_report_convertor = VelocityReportConvertor(tasks_container.assignee_search_api)
        return self._velocity_report_convertor

    def _get_task_forecast_chart_convertor(self) -> TaskForecastChartConvertor:
        if self._task_forecast_chart_convertor is None:
            self._task_forecast_chart_convertor = TaskForecastChartConvertor()
        return self._task_forecast_chart_convertor


ui_web_container = UiWebContainer()
