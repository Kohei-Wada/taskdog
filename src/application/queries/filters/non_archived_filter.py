"""Filter for non-deleted tasks."""

from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task


class NonArchivedFilter(TaskFilter):
    """Filter tasks that are not deleted.

    Returns tasks with is_deleted=False.
    Kept name for backward compatibility but now filters by is_deleted flag.
    """

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter non-deleted tasks.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks that are not deleted
        """
        return [task for task in tasks if not task.is_deleted]
