from enum import Enum, auto


class TargetType(Enum):
    TASK = "task"


class SubjectType(Enum):
    MEMBER = "member"
    MEMBER_GROUP = "member_group"


class ForecastCalculationType(Enum):
    IDEAL_VELOCITY = auto()
    REAL_VELOCITY = auto()


class ForecastScope(Enum):
    DIRECT = auto()
    CUMULATIVE_HIERARCHY = auto()


class VelocityStrategy(Enum):
    IDEAL_VELOCITY = auto()
    REAL_VELOCITY = auto()


class StoryPointsStrategy(Enum):
    DIRECT = auto()
    CUMULATIVE = auto()