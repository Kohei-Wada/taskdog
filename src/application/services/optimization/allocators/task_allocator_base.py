"""Abstract base class for task allocation strategies."""

from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.task import Task


class TaskAllocatorBase(ABC):
    """Abstract base class for task allocation strategies.

    Allocators are responsible for determining when and how to schedule
    a single task given current resource constraints.

    Each allocator implements a specific scheduling algorithm (greedy,
    balanced, backward, etc.) while the sorting of tasks is handled
    separately by the optimization strategy.
    """

    @abstractmethod
    def allocate(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
        daily_allocations: dict[str, float],
        repository,
    ) -> Task | None:
        """Allocate time blocks for a single task.

        Args:
            task: Task to schedule
            start_date: Earliest allowed start date
            max_hours_per_day: Maximum work hours per day
            daily_allocations: Current daily allocations (will be modified)
            repository: Task repository for deadline calculations

        Returns:
            Copy of task with updated schedule (planned_start, planned_end,
            daily_allocations), or None if allocation fails
        """
        pass

    def _is_weekend(self, date: datetime) -> bool:
        """Check if a date is a weekend.

        Args:
            date: Date to check

        Returns:
            True if Saturday or Sunday, False otherwise
        """
        return date.weekday() >= 5  # Saturday=5, Sunday=6

    def _count_weekdays(self, start_date: datetime, end_date: datetime) -> int:
        """Count weekdays between start and end date (inclusive).

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of weekdays (Monday-Friday)
        """
        from datetime import timedelta

        count = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Monday=0 to Friday=4
                count += 1
            current += timedelta(days=1)
        return count
