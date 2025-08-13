from sd_metrics_lib.utils.time import TimeUnit, Duration


class EstimationTimeCalculator:

    @staticmethod
    def estimate(story_points: float, velocity: float, time_unit: TimeUnit) -> Duration | None:
        if story_points is None or velocity is None or velocity <= 0:
            return None

        estimation_in_units = story_points / velocity
        return Duration.of(estimation_in_units, time_unit)
