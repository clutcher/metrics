from typing import List, Set

from .assignee_search_service import AssigneeSearchService
from .convertors.task_metadata_convertor import TaskMetadataPopulator
from .model.config import TasksConfig
from .model.task import Task, HierarchyTraversalCriteria, TaskSearchCriteria, TaskStatus
from ..api.api_for_task_hierarchy import ApiForTaskHierarchy
from ..spi.task_repository import TaskRepository


class TaskHierarchyService(ApiForTaskHierarchy):

    def __init__(self, repository: TaskRepository, task_config: TasksConfig,
                 assignee_search_service: AssigneeSearchService,
                 metadata_convertor: TaskMetadataPopulator):
        self._repository = repository
        self._config = task_config
        self._assignee_search_api = assignee_search_service
        self._metadata_convertor = metadata_convertor

    async def get_tasks_with_full_hierarchy(self, task_ids: List[str], criteria: HierarchyTraversalCriteria) -> List[
        Task]:
        task_criteria = TaskSearchCriteria(id_filter=task_ids)
        tasks = await self._repository.find_all(search_criteria=task_criteria)

        if not tasks:
            return []

        tasks_with_hierarchy = []
        for task in tasks:
            self._metadata_convertor.populate_metadata(task)

            visited_tasks: Set[str] = set()
            await self._traverse_hierarchy(task, criteria, visited_tasks, 0)

            tasks_with_hierarchy.append(task)

        self._assignee_search_api.populate_assignee_cache_from_tasks(tasks_with_hierarchy)

        return tasks_with_hierarchy

    async def _traverse_hierarchy(self, task: Task, criteria: HierarchyTraversalCriteria,
                                  visited_tasks: Set[str], current_depth: int) -> None:
        if current_depth >= criteria.max_depth or task.id in visited_tasks:
            return

        if criteria.exclude_done_tasks and self._is_task_done(task):
            return

        await self._load_complete_hierarchy(task, visited_tasks, criteria)
        self._prune_hierarchy_to_max_depth(task, criteria.max_depth, current_depth)
        self._apply_task_filters(task, criteria)
        self._ensure_metadata_populated(task)

    async def _load_complete_hierarchy(self, root_task: Task, visited_tasks: Set[str],
                                       criteria: HierarchyTraversalCriteria) -> None:
        tasks_to_explore = [root_task]
        current_depth = 0

        while tasks_to_explore and current_depth < criteria.max_depth:
            tasks_needing_children = []
            for task in tasks_to_explore:
                tasks_needing_children.extend(self._collect_all_tasks_needing_children(task, visited_tasks))

            filtered_tasks_needing_children = [
                task for task in tasks_needing_children
                if self._should_include_task(task, criteria)
            ]

            if not filtered_tasks_needing_children:
                break

            await self._batch_load_children_for_tasks(filtered_tasks_needing_children)

            next_tasks_to_explore = []
            for task in tasks_needing_children:
                visited_tasks.add(task.id)
                if task.child_tasks:
                    next_tasks_to_explore.extend(task.child_tasks)

            tasks_to_explore = next_tasks_to_explore
            current_depth += 1

    async def _batch_load_children_for_tasks(self, parent_tasks: List[Task]) -> None:
        if not parent_tasks:
            return

        parent_task_ids = [task.id for task in parent_tasks]
        task_criteria = TaskSearchCriteria(id_filter=parent_task_ids)
        tasks_with_children = await self._repository.find_all(search_criteria=task_criteria)

        if not tasks_with_children:
            return

        task_children_map = {}
        for task in tasks_with_children:
            if task.child_tasks:
                task_children_map[task.id] = task.child_tasks

        for parent_task in parent_tasks:
            if parent_task.id in task_children_map:
                parent_task.child_tasks = task_children_map[parent_task.id]

    def _collect_all_tasks_needing_children(self, root_task: Task, visited_tasks: Set[str]) -> List[Task]:
        tasks_needing_children = []
        self._traverse_for_missing_children(root_task, visited_tasks, tasks_needing_children)
        return tasks_needing_children

    def _traverse_for_missing_children(self, task: Task, visited_tasks: Set[str],
                                       result_list: List[Task]) -> None:
        if task.id in visited_tasks:
            return
            
        visited_tasks.add(task.id)
        
        if not task.child_tasks:
            result_list.append(task)
        else:
            for child_task in task.child_tasks:
                self._traverse_for_missing_children(child_task, visited_tasks, result_list)

    def _apply_task_filters(self, task: Task, criteria: HierarchyTraversalCriteria) -> None:
        if task.child_tasks:
            filtered_children = []
            for child_task in task.child_tasks:
                self._apply_task_filters(child_task, criteria)

                if self._should_include_task(child_task, criteria):
                    filtered_children.append(child_task)

            task.child_tasks = filtered_children if filtered_children else None

    def _should_include_task(self, task: Task, criteria: HierarchyTraversalCriteria) -> bool:
        if criteria.exclude_done_tasks and self._is_task_done(task):
            return False
        if criteria.only_tasks_with_story_points and not self._has_story_points(task):
            return False
        return True

    def _ensure_metadata_populated(self, task: Task) -> None:
        self._metadata_convertor.populate_metadata(task)

        if task.child_tasks:
            for child_task in task.child_tasks:
                self._ensure_metadata_populated(child_task)

    def _prune_hierarchy_to_max_depth(self, task: Task, max_depth: int, current_depth: int) -> None:
        if current_depth + 1 >= max_depth:
            task.child_tasks = None
            return

        if task.child_tasks:
            for child_task in task.child_tasks:
                self._prune_hierarchy_to_max_depth(child_task, max_depth, current_depth + 1)

    @staticmethod
    def _is_task_done(task: Task) -> bool:
        return task.status == TaskStatus.DONE

    @staticmethod
    def _has_story_points(task: Task) -> bool:
        return task.story_points is not None and task.story_points > 0
    
