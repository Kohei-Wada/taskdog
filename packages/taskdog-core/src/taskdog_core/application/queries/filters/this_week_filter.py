"""Filter for this week's tasks."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import Task, TaskStatus

if TYPE_CHECKING:
    from taskdog_core.domain.services.time_provider import ITimeProvider


class ThisWeekFilter(TaskFilter):
    """Filter tasks relevant for this week.

    Identifies tasks that meet any of these criteria:
    - Deadline is within this week (Monday to Sunday)
    - Planned period overlaps with this week
    - Status is IN_PROGRESS
    """

    def __init__(
        self,
        include_completed: bool = False,
        time_provider: ITimeProvider | None = None,
    ):
        """Initialize filter.

        Args:
            include_completed: Whether to include completed tasks
            time_provider: Provider for current time. Defaults to SystemTimeProvider.
        """
        self.include_completed = include_completed
        if time_provider is None:
            from taskdog_core.infrastructure.time_provider import SystemTimeProvider

            time_provider = SystemTimeProvider()
        self._time_provider = time_provider

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks that are relevant for this week.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks matching this week's criteria
        """
        today = self._time_provider.today()

        # Calculate this week's range (Monday to Sunday)
        # weekday(): Monday=0, Sunday=6
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        matching_tasks = []

        for task in tasks:
            # Always skip archived tasks (historical records, not relevant to this week)
            if not task.can_be_modified:
                continue

            # Skip completed tasks unless include_completed is True
            if not self.include_completed and task.status == TaskStatus.COMPLETED:
                continue

            # Check if task matches this week's criteria
            if self._is_this_week_task(task, week_start, week_end):
                matching_tasks.append(task)

        return matching_tasks

    def _is_this_week_task(self, task: Task, week_start: date, week_end: date) -> bool:
        """Check if a task is relevant for this week.

        Args:
            task: Task to check
            week_start: Start of this week (Monday)
            week_end: End of this week (Sunday)

        Returns:
            True if task meets any of this week's criteria
        """
        # Criterion A: Deadline is within this week
        if task.deadline:
            deadline_date = task.deadline.date()
            if week_start <= deadline_date <= week_end:
                return True

        # Criterion B: Planned period overlaps with this week
        if task.planned_start and task.planned_end:
            planned_start_date = task.planned_start.date()
            planned_end_date = task.planned_end.date()
            # Check if ranges overlap
            if planned_start_date <= week_end and planned_end_date >= week_start:
                return True

        # Criterion C: Status is IN_PROGRESS
        return task.status == TaskStatus.IN_PROGRESS
