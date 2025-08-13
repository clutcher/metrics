import unittest

from sd_metrics_lib.utils.enums import HealthStatus
from sd_metrics_lib.utils.time import Duration, TimeUnit

from forecast.app.domain.calculation.health import HealthStatusCalculator


class TestHealthStatusCalculator(unittest.TestCase):

    def test_shouldReturnGreenWhenNoTimeSpent(self):
        estimation_time = Duration.of(10.0, TimeUnit.HOUR)
        total_spent_time = None
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.GREEN, result)

    def test_shouldReturnGreenWhenSpentTimeLessThanEstimation(self):
        estimation_time = Duration.of(10.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(8.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.GREEN, result)

    def test_shouldReturnGreenWhenSpentTimeExactlyEqualsEstimation(self):
        estimation_time = Duration.of(10.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(10.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.GREEN, result)

    def test_shouldReturnYellowWhenSpentTimeExceeds100PercentButLessThan140Percent(self):
        estimation_time = Duration.of(10.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(12.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.YELLOW, result)

    def test_shouldReturnYellowAtExactly140PercentBoundary(self):
        estimation_time = Duration.of(10.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(14.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.YELLOW, result)

    def test_shouldReturnOrangeWhenSpentTimeExceeds140PercentButLessThan200Percent(self):
        estimation_time = Duration.of(10.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(18.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.ORANGE, result)

    def test_shouldReturnOrangeAtExactly200PercentBoundary(self):
        estimation_time = Duration.of(10.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(20.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.ORANGE, result)

    def test_shouldReturnRedWhenSpentTimeMoreThanTwiceTheEstimation(self):
        estimation_time = Duration.of(10.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(25.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.RED, result)

    def test_shouldReturnGrayWhenEstimationTimeIsZero(self):
        estimation_time = Duration.of(0.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(5.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.GRAY, result)

    def test_shouldReturnGrayWhenEstimationTimeIsNegative(self):
        estimation_time = Duration.of(-1.0, TimeUnit.HOUR)
        total_spent_time = Duration.of(5.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.GRAY, result)

    def test_shouldHandleDifferentTimeUnitsCorrectly(self):
        estimation_time = Duration.of(1.0, TimeUnit.DAY)
        total_spent_time = Duration.of(12.0, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.ORANGE, result)

    def test_shouldHandleVerySmallDurations(self):
        estimation_time = Duration.of(0.1, TimeUnit.HOUR)
        total_spent_time = Duration.of(0.15, TimeUnit.HOUR)
        
        result = HealthStatusCalculator.calculate(estimation_time, total_spent_time)
        
        self.assertEqual(HealthStatus.ORANGE, result)


if __name__ == '__main__':
    unittest.main()