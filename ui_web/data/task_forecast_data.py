from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from .task_data import TaskData


@dataclass(slots=True)
class TaskForecastParamsData:
    task_id: Optional[str] = None
    start_date: Optional[str] = None
    member_group: Optional[str] = None
    time_unit: str = 'day'


@dataclass(slots=True)
class TaskForecastBreakdownItem:
    task_id: str
    task_title: str
    estimation_days: float
    level: int
    has_children: bool


@dataclass(slots=True)
class TaskForecastSummaryData:
    task_title: str
    total_estimation_days: float
    forecasted_start_date: datetime
    forecasted_end_date: datetime
    average_team_velocity: Optional[float]
    task_forecasts: List[TaskForecastBreakdownItem]


@dataclass(slots=True)
class TaskForecastRequestData:
    task_id: Optional[str] = None
    start_date: Optional[str] = None
    member_group: Optional[str] = None


@dataclass(slots=True)
class TaskForecastData:
    root_task: Optional[TaskData]
    task_forecast: Optional[TaskForecastSummaryData]
    chart_data: str
    task_id: Optional[str]
    start_date: Optional[str] 
    member_group: Optional[str]
    time_unit: str
    success: bool
    error: Optional[str] = None