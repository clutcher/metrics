from django.conf import settings

from .app.domain.model.config import VelocityConfig, CalculationConfig, WorkflowConfig, MemberVelocityConfig


def load_velocity_config() -> VelocityConfig:
    calculation = CalculationConfig(
        working_days_per_month=settings.METRICS_WORKING_DAYS_PER_MONTH,
        default_story_points_value_when_missing=settings.METRICS_DEFAULT_STORY_POINTS_VALUE_WHEN_MISSING
    )

    workflow = WorkflowConfig(
        done_status_codes=settings.METRICS_DONE_STATUS_CODES
    )

    member_velocity = MemberVelocityConfig(
        story_points_to_ideal_hours_ratio=settings.METRICS_STORY_POINTS_TO_IDEAL_HOURS_CONVERTION_RATIO,
        seniority_levels=settings.METRICS_SENIORITY_LEVELS,
        members=settings.METRICS_MEMBERS,
        default_seniority_level=settings.METRICS_DEFAULT_SENIORITY_LEVEL_WHEN_MISSING,
    )

    return VelocityConfig(
        calculation=calculation,
        workflow=workflow,
        member_velocity=member_velocity
    )
