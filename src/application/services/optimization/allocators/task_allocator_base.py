"""Abstract base class for task allocation strategies."""

import copy
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from domain.entities.task import Task
from shared.config_manager import Config
from shared.utils.date_utils import is_workday

if TYPE_CHECKING:
    from shared.utils.holiday_checker import HolidayChecker


class TaskAllocatorBase(ABC):
    """Abstract base class for task allocation strategies.

    Allocators are responsible for determining when and how to schedule
    a single task given current resource constraints.

    Each allocator implements a specific scheduling algorithm (greedy,
    balanced, backward, etc.) while the sorting of tasks is handled
    separately by the optimization strategy.
    """

    def __init__(self, config: Config, holiday_checker: "HolidayChecker | None" = None):
        """Initialize allocator with configuration.

        Args:
            config: Application configuration
            holiday_checker: Optional HolidayChecker for holiday detection
        """
        self.config = config
        self.holiday_checker = holiday_checker

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

    # Helper methods for subclasses

    def _validate_task(self, task: Task) -> bool:
        """Validate task has required fields for allocation.

        Args:
            task: Task to validate

        Returns:
            True if task is valid for allocation, False otherwise
        """
        return task.estimated_duration is not None and task.estimated_duration > 0

    def _create_task_copy(self, task: Task) -> Task:
        """Create a deep copy of task for modification.

        Args:
            task: Original task

        Returns:
            Deep copy of task with type assertion on estimated_duration
        """
        task_copy = copy.deepcopy(task)
        # Type narrowing: guaranteed by _validate_task
        assert task_copy.estimated_duration is not None
        return task_copy

    def _get_effective_deadline(self, task: Task) -> datetime | None:
        """Get effective deadline for task scheduling.

        Args:
            task: Task to get deadline for

        Returns:
            Effective deadline datetime, or None if no deadline
        """
        return task.deadline

    def _get_date_str(self, date: datetime) -> str:
        """Convert datetime to date string format.

        Args:
            date: Datetime to convert

        Returns:
            Date string in YYYY-MM-DD format
        """
        return date.strftime("%Y-%m-%d")

    def _get_next_workday(self, current_date: datetime, direction: int = 1) -> datetime:
        """Get next workday, skipping weekends and holidays.

        Args:
            current_date: Starting date
            direction: 1 for forward, -1 for backward

        Returns:
            Next workday in specified direction
        """
        next_date = current_date + timedelta(days=direction)
        while not is_workday(next_date, self.holiday_checker):
            next_date += timedelta(days=direction)
        return next_date

    def _get_current_allocation(self, daily_allocations: dict[str, float], date_str: str) -> float:
        """Get current allocation for a specific date.

        Args:
            daily_allocations: Current daily allocations
            date_str: Date string to look up

        Returns:
            Current allocation hours for the date
        """
        return daily_allocations.get(date_str, 0.0)

    def _calculate_available_hours(
        self, daily_allocations: dict[str, float], date_str: str, max_hours_per_day: float
    ) -> float:
        """Calculate available hours for a specific date.

        Args:
            daily_allocations: Current daily allocations
            date_str: Date string to check
            max_hours_per_day: Maximum hours per day

        Returns:
            Available hours for the date
        """
        current_allocation = self._get_current_allocation(daily_allocations, date_str)
        return max_hours_per_day - current_allocation

    def _set_planned_times(
        self,
        task: Task,
        schedule_start: datetime,
        schedule_end: datetime,
        task_daily_allocations: dict[str, float],
    ) -> None:
        """Set planned start, end, and daily allocations on task.

        Args:
            task: Task to update
            schedule_start: Start datetime
            schedule_end: End datetime
            task_daily_allocations: Daily allocation hours
        """
        # Set start time to config.time.default_start_hour (default: 9:00)
        start_date_with_time = schedule_start.replace(
            hour=self.config.time.default_start_hour, minute=0, second=0
        )
        task.planned_start = start_date_with_time

        # Set end time to config.time.default_end_hour (default: 18:00)
        end_date_with_time = schedule_end.replace(
            hour=self.config.time.default_end_hour, minute=0, second=0
        )
        task.planned_end = end_date_with_time
        task.daily_allocations = task_daily_allocations

    def _rollback_allocations(
        self, daily_allocations: dict[str, float], task_allocations: dict[str, float]
    ) -> None:
        """Rollback allocations from daily_allocations.

        Args:
            daily_allocations: Global daily allocations to rollback
            task_allocations: Task-specific allocations to remove
        """
        for date_str, hours in task_allocations.items():
            daily_allocations[date_str] -= hours
