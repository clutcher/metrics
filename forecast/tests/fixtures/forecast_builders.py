from datetime import datetime

from sd_metrics_lib.utils.time import TimeUnit

from forecast.app.domain.model.enums import VelocityStrategy, StoryPointsStrategy, SubjectType
from forecast.app.domain.model.forecast import ForecastGenerationParameters, Subject


class ForecastParametersBuilder:
    
    def __init__(self):
        self._velocity_strategy = VelocityStrategy.REAL_VELOCITY
        self._story_points_strategy = StoryPointsStrategy.DIRECT
        self._subject = Subject(type=SubjectType.MEMBER, id="john.doe")
        self._time_unit = TimeUnit.HOUR
        self._start_date = datetime(2024, 1, 15, 9, 0, 0)
    
    @classmethod
    def default_parameters(cls) -> 'ForecastParametersBuilder':
        return cls()
    
    @classmethod
    def sprint_planning_parameters(cls) -> 'ForecastParametersBuilder':
        return cls().for_sprint_start()
    
    @classmethod
    def project_estimation_parameters(cls) -> 'ForecastParametersBuilder':
        return (cls()
                .using_ideal_velocity()
                .for_member_group("backend-team")
                .in_days())
    
    def using_ideal_velocity(self) -> 'ForecastParametersBuilder':
        self._velocity_strategy = VelocityStrategy.IDEAL_VELOCITY
        return self
    
    def using_real_velocity(self) -> 'ForecastParametersBuilder':
        self._velocity_strategy = VelocityStrategy.REAL_VELOCITY
        return self
    
    def with_direct_story_points(self) -> 'ForecastParametersBuilder':
        self._story_points_strategy = StoryPointsStrategy.DIRECT
        return self
    
    def with_cumulative_story_points(self) -> 'ForecastParametersBuilder':
        self._story_points_strategy = StoryPointsStrategy.CUMULATIVE
        return self
    
    def for_developer(self, developer_id: str) -> 'ForecastParametersBuilder':
        self._subject = Subject(type=SubjectType.MEMBER, id=developer_id)
        return self
    
    def for_member_group(self, group_id: str) -> 'ForecastParametersBuilder':
        self._subject = Subject(type=SubjectType.MEMBER_GROUP, id=group_id)
        return self
    
    def in_hours(self) -> 'ForecastParametersBuilder':
        self._time_unit = TimeUnit.HOUR
        return self
    
    def in_days(self) -> 'ForecastParametersBuilder':
        self._time_unit = TimeUnit.DAY
        return self
    
    def for_sprint_start(self) -> 'ForecastParametersBuilder':
        self._start_date = datetime(2024, 1, 15, 9, 0, 0)
        return self
    
    def starting_on(self, start_date: datetime) -> 'ForecastParametersBuilder':
        self._start_date = start_date
        return self
    
    def build(self) -> ForecastGenerationParameters:
        return ForecastGenerationParameters(
            velocity_strategy=self._velocity_strategy,
            story_points_strategy=self._story_points_strategy,
            subject=self._subject,
            time_unit=self._time_unit,
            start_date=self._start_date
        )


class BusinessVelocityScenarios:
    
    @staticmethod
    def high_performing_team_velocity() -> float:
        return 2.5
    
    @staticmethod
    def average_team_velocity() -> float:
        return 1.5
    
    @staticmethod
    def struggling_team_velocity() -> float:
        return 0.8
    
    @staticmethod
    def senior_developer_velocity() -> float:
        return 3.0
    
    @staticmethod
    def junior_developer_velocity() -> float:
        return 1.2
    
    @staticmethod
    def no_velocity_available() -> None:
        return None