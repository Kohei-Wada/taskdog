"""Filter for incomplete or active tasks."""

from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class IncompleteOrActiveFilter(TaskFilter):
    """Filter tasks that are incomplete or active.

    Returns tasks with status != COMPLETED and status != CANCELED.
    Excludes finished tasks (completed/canceled) from the result set.
    """

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter incomplete or active tasks.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks that are not completed or canceled
        """
        return [
            task
            for task in tasks
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELED)
        ]
