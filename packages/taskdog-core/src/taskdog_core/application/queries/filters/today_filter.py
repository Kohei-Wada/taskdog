"""Filter for today's tasks."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import Task, TaskStatus

if TYPE_CHECKING:
    from taskdog_core.domain.services.time_provider import ITimeProvider


class TodayFilter(TaskFilter):
    """Filter tasks relevant for today.

    Identifies tasks that meet any of these criteria:
    - Deadline is today
    - Planned period includes today (planned_start <= today <= planned_end)
    - Status is IN_PROGRESS

    This filter should be combined with other filters (e.g., IncompleteFilter)
    using CompositeFilter for proper filtering behavior.
    """

    def __init__(self, time_provider: ITimeProvider | None = None):
        """Initialize filter with optional time provider.

        Args:
            time_provider: Provider for current time. Defaults to SystemTimeProvider.
        """
        if time_provider is None:
            from taskdog_core.infrastructure.time_provider import SystemTimeProvider

            time_provider = SystemTimeProvider()
        self._time_provider = time_provider

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks that are relevant for today.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks matching today's criteria
        """
        today = self._time_provider.today()

        matching_tasks = []

        for task in tasks:
            # Check if task matches today's criteria
            if self._is_today_task(task, today):
                matching_tasks.append(task)

        return matching_tasks

    def _is_today_task(self, task: Task, today: date) -> bool:
        """Check if a task is relevant for today.

        Args:
            task: Task to check
            today: Today's date (datetime.date object)

        Returns:
            True if task meets any of today's criteria
        """
        # Criterion A: Deadline is today
        if task.deadline:
            deadline_date = task.deadline.date()
            if deadline_date == today:
                return True

        # Criterion B: Planned period includes today
        if task.planned_start and task.planned_end:
            planned_start_date = task.planned_start.date()
            planned_end_date = task.planned_end.date()
            if planned_start_date <= today <= planned_end_date:
                return True

        # Criterion C: Status is IN_PROGRESS
        return task.status == TaskStatus.IN_PROGRESS
