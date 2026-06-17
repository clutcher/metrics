from typing import Any, Dict, List, Optional, Tuple

from ..model.pull_request import Reviewer, ReviewTier

_TIER_RANK = {
    ReviewTier.MAIN: 0,
    ReviewTier.ADDITIONAL: 1,
}


class ReviewerSeniority:

    def __init__(self, members: Dict[str, Dict[str, Any]], main_reviewer_levels: List[str],
                 seniority_levels: Dict[str, float]):
        self._levels_by_member = {name: data.get('level') for name, data in members.items()}
        self._main_reviewer_levels = {level.lower() for level in main_reviewer_levels}
        self._level_rank = self._build_level_rank(seniority_levels)

    def resolve_level(self, display_name: str) -> Optional[str]:
        return self._levels_by_member.get(display_name)

    def resolve_tier(self, display_name: str) -> ReviewTier:
        level = self.resolve_level(display_name)
        if level is not None and level.lower() in self._main_reviewer_levels:
            return ReviewTier.MAIN
        return ReviewTier.ADDITIONAL

    def approval_sort_key(self, reviewer: Reviewer) -> Tuple[int, int, str]:
        level_rank = self._level_rank.get((reviewer.level or '').lower(), len(self._level_rank))
        return _TIER_RANK[reviewer.tier], level_rank, reviewer.display_name.lower()

    @staticmethod
    def _build_level_rank(seniority_levels: Dict[str, float]) -> Dict[str, int]:
        ordered_levels = sorted(seniority_levels.items(), key=lambda level_multiplier: level_multiplier[1])
        return {level.lower(): rank for rank, (level, _) in enumerate(ordered_levels)}
