"""Task query service for read-optimized operations."""

from application.queries.base import QueryService
from application.queries.filters.task_sorter import TaskSorter
from application.queries.filters.today_filter import TodayFilter
from domain.entities.task import Task, TaskStatus


class TaskQueryService(QueryService):
    """Query service for task read operations.

    Provides read-only operations with filtering, sorting, and other
    query-specific logic. Optimized for data retrieval without state modification.
    """

    def __init__(self, repository):
        """Initialize query service with repository.

        Args:
            repository: Task repository for data access
        """
        super().__init__(repository)
        self.today_filter = TodayFilter(repository)
        self.sorter = TaskSorter()

    def get_today_tasks(self, include_completed: bool = False) -> list[Task]:
        """Get tasks relevant for today.

        Returns tasks that meet any of these criteria:
        - Deadline is today
        - Planned period includes today
        - Status is IN_PROGRESS

        Tasks are sorted by deadline -> priority -> id.
        Ancestor tasks are included to preserve hierarchy.

        Args:
            include_completed: Whether to include completed tasks

        Returns:
            Filtered and sorted list of today's tasks
        """
        tasks = self.repository.get_all()
        filtered_tasks = self.today_filter.filter(tasks, include_completed)
        sorted_tasks = self.sorter.sort(filtered_tasks)
        return sorted_tasks

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks without filtering.

        Returns:
            List of all tasks
        """
        return self.repository.get_all()

    def get_incomplete_tasks_with_hierarchy(self) -> list[Task]:
        """Get incomplete tasks, preserving hierarchy by including necessary ancestors.

        Completed parent tasks are included if they have incomplete descendants.
        Used by tree view to show meaningful hierarchy while hiding fully completed branches.

        Returns:
            List of incomplete tasks with necessary ancestor tasks
        """
        tasks = self.repository.get_all()

        # Get all incomplete task IDs
        incomplete_ids = {t.id for t in tasks if t.status != TaskStatus.COMPLETED}

        # Get all ancestor IDs of incomplete tasks
        ancestor_ids = set()
        for task in tasks:
            if task.id in incomplete_ids:
                # Add all ancestors
                current = task
                while current.parent_id:
                    ancestor_ids.add(current.parent_id)
                    current = self.repository.get_by_id(current.parent_id)
                    if not current:
                        break

        # Include incomplete tasks and their necessary ancestors
        included_ids = incomplete_ids | ancestor_ids
        return [t for t in tasks if t.id in included_ids]

    def get_incomplete_tasks(self) -> list[Task]:
        """Get only incomplete tasks without hierarchy preservation.

        Returns tasks with status PENDING, IN_PROGRESS, or FAILED.
        Used by flat views like table.

        Returns:
            List of incomplete tasks
        """
        tasks = self.repository.get_all()
        return [t for t in tasks if t.status != TaskStatus.COMPLETED]
