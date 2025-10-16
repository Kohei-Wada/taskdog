"""Task query service for read-optimized operations."""

from application.queries.base import QueryService
from application.queries.filters.task_filter import TaskFilter
from application.queries.filters.task_sorter import TaskSorter
from domain.entities.task import Task


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
        self.sorter = TaskSorter()

    def get_filtered_tasks(
        self,
        filter_obj: TaskFilter | None = None,
        sort_by: str = "id",
        reverse: bool = False,
    ) -> list[Task]:
        """Get tasks with optional filtering and sorting.

        Args:
            filter_obj: Optional filter object to apply. If None, returns all tasks.
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)

        Returns:
            Filtered and sorted list of tasks
        """
        tasks = self.repository.get_all()

        # Apply filter if provided
        if filter_obj:
            tasks = filter_obj.filter(tasks)

        # Sort tasks
        return self.sorter.sort(tasks, sort_by, reverse)
