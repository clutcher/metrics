import unittest

from sd_metrics_lib.utils.time import TimePolicy

from tasks.tests.fixtures.task_builders import TaskBuilder
from ui_web.convertors.task_convertor import TaskConvertor


class TestTaskConvertorIteration(unittest.TestCase):

    def test_shouldPassThroughIterationFromDomainToData(self):
        # given
        task = (TaskBuilder.sprint_story()
                .assigned_to_senior_developer()
                .with_iteration("Sprint 12")
                .build())
        convertor = TaskConvertor(TimePolicy.BUSINESS_HOURS)

        # when
        task_data = convertor.convert_task_to_data(task)

        # then
        self.assertEqual("Sprint 12", task_data.iteration)

    def test_shouldLeaveIterationNoneOnDataWhenDomainTaskHasNoIteration(self):
        # given
        task = TaskBuilder.sprint_story().assigned_to_senior_developer().build()
        convertor = TaskConvertor(TimePolicy.BUSINESS_HOURS)

        # when
        task_data = convertor.convert_task_to_data(task)

        # then
        self.assertIsNone(task_data.iteration)


if __name__ == '__main__':
    unittest.main()
