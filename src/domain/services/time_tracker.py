from datetime import datetime

from domain.entities.task import Task, TaskStatus


class TimeTracker:
    """Handles automatic time tracking for tasks."""

    def record_time_on_status_change(self, task: Task, new_status: TaskStatus) -> None:
        """Record timestamps when task status changes.

        Args:
            task: The task being updated
            new_status: The new status being set

        Side effects:
            Modifies task.actual_start when status becomes IN_PROGRESS
            Modifies task.actual_end when status becomes COMPLETED or CANCELED
        """
        now = datetime.now()

        # Record actual start when moving to IN_PROGRESS
        if new_status == TaskStatus.IN_PROGRESS and not task.actual_start:
            task.actual_start = now

        # Record actual end when moving to COMPLETED or CANCELED
        if new_status in [TaskStatus.COMPLETED, TaskStatus.CANCELED] and not task.actual_end:
            task.actual_end = now

    def clear_time_on_pause(self, task: Task) -> None:
        """Clear time tracking fields when task is paused.

        Args:
            task: The task being paused

        Side effects:
            Clears task.actual_start and task.actual_end
        """
        task.actual_start = None
        task.actual_end = None

    def clear_time_on_reopen(self, task: Task) -> None:
        """Clear time tracking fields when task is reopened.

        Args:
            task: The task being reopened

        Side effects:
            Clears task.actual_start and task.actual_end
        """
        task.actual_start = None
        task.actual_end = None
