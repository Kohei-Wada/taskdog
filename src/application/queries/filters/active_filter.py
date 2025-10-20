"""Filter for active (non-deleted) tasks."""

from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task


class ActiveFilter(TaskFilter):
    """Filter tasks that are not deleted.

    Returns tasks with is_deleted=False.
    Used for showing all active tasks including completed ones.
    """

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter active (non-archived) tasks.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks that are not archived
        """
        return [task for task in tasks if not task.is_deleted]
