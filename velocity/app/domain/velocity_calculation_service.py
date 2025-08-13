from typing import Optional

from sd_metrics_lib.utils.time import Duration, TimePolicy, TimeUnit

from .model.config import MemberVelocityConfig
from ..api.api_for_velocity_calculation import ApiForVelocityCalculation


class VelocityCalculationService(ApiForVelocityCalculation):

    def __init__(self, member_velocity_config: MemberVelocityConfig, ideal_time_policy: TimePolicy):
        self._config = member_velocity_config
        self._ideal_time_policy = ideal_time_policy

    async def calculate_ideal_velocity(self, member_id: str, time_unit: TimeUnit) -> Optional[float]:
        if member_id is None:
            return None

        base_time_per_story_point = self._base_time_per_story_point_duration()
        if base_time_per_story_point is None or base_time_per_story_point.is_zero():
            return None

        member_multiplier = self._get_member_seniority_multiplier(member_id)
        effective_time_per_story_point = base_time_per_story_point if member_multiplier is None else base_time_per_story_point * member_multiplier

        time_needed_to_complete_single_story_point = effective_time_per_story_point.convert(time_unit,
                                                                                            self._ideal_time_policy)
        if time_needed_to_complete_single_story_point <= Duration.zero():
            return None

        velocity = 1.0 / time_needed_to_complete_single_story_point.time_delta
        return velocity

    def _base_time_per_story_point_duration(self) -> Optional[Duration]:
        hours_per_story_point = self._config.story_points_to_ideal_hours_ratio
        if hours_per_story_point is None or hours_per_story_point <= 0:
            return None
        return Duration.of(hours_per_story_point, TimeUnit.HOUR)

    def _get_member_seniority_multiplier(self, member_id: str) -> Optional[float]:
        member_seniority_level = self._get_member_seniority_level(member_id)
        if member_seniority_level not in self._config.seniority_levels:
            return None

        multiplier = self._config.seniority_levels[member_seniority_level]
        return multiplier

    def _get_member_seniority_level(self, member_id: str) -> Optional[str]:
        member_data = self._config.members.get(member_id, {})

        member_level = member_data.get('level')
        if member_level:
            return member_level

        default_level = self._config.default_seniority_level
        return default_level
