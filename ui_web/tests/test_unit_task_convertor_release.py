import unittest

from sd_metrics_lib.utils.time import TimePolicy

from tasks.tests.fixtures.task_builders import TaskBuilder
from ui_web.convertors.task_convertor import TaskConvertor


class TestTaskConvertorRelease(unittest.TestCase):

    def test_shouldPassThroughReleasesFromDomainToData(self):
        # given
        task = (TaskBuilder.sprint_story()
                .assigned_to_senior_developer()
                .with_releases("2026.015", "2026.016")
                .build())
        convertor = TaskConvertor(TimePolicy.BUSINESS_HOURS)

        # when
        task_data = convertor.convert_task_to_data(task)

        # then
        self.assertEqual(2, len(task_data.releases))
        self.assertEqual("2026.015", task_data.releases[0].name)
        self.assertEqual("2026.016", task_data.releases[1].name)

    def test_shouldLeaveReleasesNoneOnDataWhenDomainTaskHasNoReleases(self):
        # given
        task = TaskBuilder.sprint_story().assigned_to_senior_developer().build()
        convertor = TaskConvertor(TimePolicy.BUSINESS_HOURS)

        # when
        task_data = convertor.convert_task_to_data(task)

        # then
        self.assertIsNone(task_data.releases)
