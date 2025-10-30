"""Filter for non-archived tasks."""

from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task


class NonArchivedFilter(TaskFilter):
    """Filter tasks that are not archived.

    Returns tasks with is_archived=False.
    Excludes archived tasks from the result set.
    """

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter non-archived tasks.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks that are not archived
        """
        return [task for task in tasks if not task.is_archived]
