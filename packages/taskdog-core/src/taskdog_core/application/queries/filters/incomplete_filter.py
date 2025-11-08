"""Filter for incomplete tasks."""

from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import Task


class IncompleteFilter(TaskFilter):
    """Filter tasks that are not yet completed.

    Returns tasks with status PENDING or IN_PROGRESS.
    Excludes COMPLETED and CANCELED tasks.
    """

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter incomplete tasks.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks that are not completed, canceled, or archived
        """
        return [task for task in tasks if not task.is_finished]
