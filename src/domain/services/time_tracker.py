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
            Modifies task.actual_end when status becomes COMPLETED or FAILED
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Record actual start when moving to IN_PROGRESS
        if new_status == TaskStatus.IN_PROGRESS and not task.actual_start:
            task.actual_start = now

        # Record actual end when moving to COMPLETED or FAILED
        if (
            new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            and not task.actual_end
        ):
            task.actual_end = now
