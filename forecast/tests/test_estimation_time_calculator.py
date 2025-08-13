import unittest

from sd_metrics_lib.utils.time import TimeUnit

from forecast.app.domain.calculation.estimation import EstimationTimeCalculator


class TestEstimationTimeCalculator(unittest.TestCase):

    def test_shouldCalculateCorrectEstimationTime(self):
        story_points = 8.0
        velocity = 2.0
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNotNone(result)
        self.assertEqual(4.0, result.time_delta)
        self.assertEqual(TimeUnit.HOUR, result.time_unit)

    def test_shouldHandleFractionalStoryPoints(self):
        story_points = 2.5
        velocity = 1.5
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNotNone(result)
        self.assertAlmostEqual(1.67, result.time_delta, places=2)
        self.assertEqual(TimeUnit.HOUR, result.time_unit)

    def test_shouldHandleDifferentTimeUnits(self):
        story_points = 10.0
        velocity = 2.0
        time_unit = TimeUnit.DAY
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNotNone(result)
        self.assertEqual(5.0, result.time_delta)
        self.assertEqual(TimeUnit.DAY, result.time_unit)

    def test_shouldReturnNullWhenStoryPointsIsNone(self):
        story_points = None
        velocity = 2.0
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNone(result)

    def test_shouldReturnNullWhenVelocityIsNone(self):
        story_points = 5.0
        velocity = None
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNone(result)

    def test_shouldReturnNullWhenVelocityIsZero(self):
        story_points = 5.0
        velocity = 0.0
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNone(result)

    def test_shouldReturnNullWhenVelocityIsNegative(self):
        story_points = 5.0
        velocity = -1.0
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNone(result)

    def test_shouldHandleZeroStoryPoints(self):
        story_points = 0.0
        velocity = 2.0
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNotNone(result)
        self.assertEqual(0.0, result.time_delta)
        self.assertEqual(TimeUnit.HOUR, result.time_unit)

    def test_shouldHandleVerySmallVelocity(self):
        story_points = 1.0
        velocity = 0.1
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNotNone(result)
        self.assertEqual(10.0, result.time_delta)
        self.assertEqual(TimeUnit.HOUR, result.time_unit)

    def test_shouldHandleVeryHighVelocity(self):
        story_points = 1.0
        velocity = 100.0
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNotNone(result)
        self.assertEqual(0.01, result.time_delta)
        self.assertEqual(TimeUnit.HOUR, result.time_unit)

    def test_shouldHandleLargeStoryPoints(self):
        story_points = 1000.0
        velocity = 2.5
        time_unit = TimeUnit.HOUR
        
        result = EstimationTimeCalculator.estimate(story_points, velocity, time_unit)
        
        self.assertIsNotNone(result)
        self.assertEqual(400.0, result.time_delta)
        self.assertEqual(TimeUnit.HOUR, result.time_unit)


if __name__ == '__main__':
    unittest.main()