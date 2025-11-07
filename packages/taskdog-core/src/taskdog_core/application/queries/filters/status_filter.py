"""Filter for tasks by status."""

from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class StatusFilter(TaskFilter):
    """Filter tasks by specific status.

    Returns tasks that match the specified status.
    """

    def __init__(self, status: TaskStatus):
        """Initialize filter with target status.

        Args:
            status: The TaskStatus to filter by
        """
        self.status = status

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks by status.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks with the specified status
        """
        return [task for task in tasks if task.status == self.status]
