from __future__ import annotations

from typing import TYPE_CHECKING

from taskdog_core.domain.entities.task import Task, TaskStatus

if TYPE_CHECKING:
    from taskdog_core.domain.services.time_provider import ITimeProvider


class TimeTracker:
    """Handles automatic time tracking for tasks."""

    def __init__(self, time_provider: ITimeProvider | None = None):
        """Initialize TimeTracker with optional time provider.

        Args:
            time_provider: Provider for current time. Defaults to SystemTimeProvider.
        """
        if time_provider is None:
            from taskdog_core.infrastructure.time_provider import SystemTimeProvider

            time_provider = SystemTimeProvider()
        self._time_provider = time_provider

    def record_time_on_status_change(self, task: Task, new_status: TaskStatus) -> None:
        """Record timestamps when task status changes.

        Args:
            task: The task being updated
            new_status: The new status being set

        Side effects:
            Modifies task.actual_start when status becomes IN_PROGRESS
            Modifies task.actual_end when status becomes COMPLETED or CANCELED
        """
        now = self._time_provider.now()

        # Record actual start when moving to IN_PROGRESS
        if new_status == TaskStatus.IN_PROGRESS and not task.actual_start:
            task.actual_start = now

        # Record actual end when moving to COMPLETED or CANCELED
        if (
            new_status in [TaskStatus.COMPLETED, TaskStatus.CANCELED]
            and not task.actual_end
        ):
            task.actual_end = now

    def clear_time_tracking(self, task: Task) -> None:
        """Clear time tracking fields.

        Used when task is paused or reopened to reset actual start/end timestamps.

        Args:
            task: The task whose time tracking should be cleared

        Side effects:
            Clears task.actual_start and task.actual_end
        """
        task.actual_start = None
        task.actual_end = None
