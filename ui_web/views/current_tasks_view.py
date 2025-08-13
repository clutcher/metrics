import asyncio
from typing import Union, List

from django.views.generic import TemplateView

from tasks.container import tasks_container
from ..container import ui_web_container
from ..data.hierarchical_item_data import HierarchicalItemData
from ..data.task_data import TaskData
from ..utils.task_grouping_utils import TaskGroupingUtils


class CurrentTasksView(TemplateView):
    template_name = "current_tasks.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tasks_facade = ui_web_container.tasks_facade
        self.members_facade = ui_web_container.members_facade
        self.workflow_config = tasks_container.get_workflow_config()

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["partials/current_tasks_content.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            group_id = self.request.GET.get('member_group_id')

            tasks = asyncio.run(self.tasks_facade.get_tasks(group_id))
            available_members = asyncio.run(
                self.members_facade.get_available_members(tasks, group_id)
            )
            grouped_tasks = self._group_tasks(tasks)

            context["tasks"] = grouped_tasks
            context["available_members"] = available_members
            context["selected_member_group_id"] = group_id
            context["has_groups"] = self._determine_has_groups(grouped_tasks)
            context["show_available_members"] = len(available_members) > 0
            context["success"] = True

        except Exception as e:
            context["error"] = str(e)
            context["success"] = False

        return context

    @staticmethod
    def _determine_has_groups(tasks: Union[List[HierarchicalItemData], List[TaskData]]) -> bool:
        return isinstance(tasks, list) and len(tasks) > 0 and isinstance(tasks[0], HierarchicalItemData)

    def _group_tasks(self, ui_tasks: List[TaskData]) -> Union[List[HierarchicalItemData], List[TaskData]]:
        return TaskGroupingUtils.group_ui_tasks_by_member_group_and_stage(ui_tasks, self.workflow_config)


class CurrentTasksChildrenView(TemplateView):
    template_name = "partials/child_task_rows.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.child_tasks_facade = ui_web_container.child_tasks_facade

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        task_id = kwargs.get("task_id")

        child_tasks = asyncio.run(self.child_tasks_facade.get_child_tasks(task_id))
        context['child_tasks'] = child_tasks
        return context
