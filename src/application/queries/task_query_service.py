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

    def get_today_tasks(
        self, include_completed: bool = False, sort_by: str = "deadline", reverse: bool = False
    ) -> list[Task]:
        """Get tasks relevant for today.

        Returns tasks that meet any of these criteria:
        - Deadline is today
        - Planned period includes today
        - Status is IN_PROGRESS

        Ancestor tasks are included to preserve hierarchy.

        Args:
            include_completed: Whether to include completed tasks
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)

        Returns:
            Filtered and sorted list of today's tasks
        """
        tasks = self.repository.get_all()
        filtered_tasks = self.today_filter.filter(tasks, include_completed)
        sorted_tasks = self.sorter.sort(filtered_tasks, sort_by, reverse)
        return sorted_tasks

    def get_all_tasks(self, sort_by: str = "id", reverse: bool = False) -> list[Task]:
        """Get all tasks without filtering.

        Args:
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)

        Returns:
            Sorted list of all tasks
        """
        tasks = self.repository.get_all()
        return self.sorter.sort(tasks, sort_by, reverse)

    def get_incomplete_tasks(self, sort_by: str = "id", reverse: bool = False) -> list[Task]:
        """Get only incomplete tasks without hierarchy preservation.

        Returns tasks with status PENDING, IN_PROGRESS, or FAILED.
        Excludes COMPLETED and ARCHIVED tasks.
        Used by flat views like table.

        Args:
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)

        Returns:
            Sorted list of incomplete tasks
        """
        tasks = self.repository.get_all()
        filtered_tasks = [
            t for t in tasks if t.status not in (TaskStatus.COMPLETED, TaskStatus.ARCHIVED)
        ]
        return self.sorter.sort(filtered_tasks, sort_by, reverse)
