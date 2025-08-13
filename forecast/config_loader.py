from django.conf import settings

from .app.domain.model.config import (
    ForecastConfig, SeniorityConfig, CalculationConfig
)


def load_forecast_config() -> ForecastConfig:
    seniority = SeniorityConfig(
        seniority_levels=settings.METRICS_SENIORITY_LEVELS,
        default_seniority_level_when_missing=settings.METRICS_DEFAULT_SENIORITY_LEVEL_WHEN_MISSING
    )

    calculation = CalculationConfig(
        ideal_hours_per_day=settings.METRICS_IDEAL_HOURS_PER_DAY,
        story_points_to_ideal_hours_convertion_ratio=settings.METRICS_STORY_POINTS_TO_IDEAL_HOURS_CONVERTION_RATIO,
        default_story_points_value_when_missing=settings.METRICS_DEFAULT_STORY_POINTS_VALUE_WHEN_MISSING,
        default_health_status_when_missing=settings.METRICS_DEFAULT_HEALTH_STATUS_WHEN_MISSING
    )

    return ForecastConfig(
        seniority=seniority,
        calculation=calculation
    )
