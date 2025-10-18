"""Deadline calculator domain service."""

from domain.entities.task import Task


class DeadlineCalculator:
    """Domain service for calculating effective deadlines.

    Returns the task's own deadline.
    """

    @staticmethod
    def get_effective_deadline(task: Task) -> str | None:
        """Get task's deadline.

        Args:
            task: Task to get deadline for

        Returns:
            Task's deadline string (YYYY-MM-DD HH:MM:SS) or None if no deadline exists
        """
        return task.deadline
