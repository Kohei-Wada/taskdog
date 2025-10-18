"""Filter for non-archived tasks."""

from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task, TaskStatus


class NonArchivedFilter(TaskFilter):
    """Filter tasks that are not archived.

    Returns tasks with status PENDING, IN_PROGRESS, FAILED, or COMPLETED.
    Excludes only ARCHIVED tasks.
    """

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter non-archived tasks.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks that are not archived
        """
        return [task for task in tasks if task.status != TaskStatus.ARCHIVED]
