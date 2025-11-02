"""Abstract base class for task allocation strategies."""

import copy
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from application.utils.date_helper import is_workday
from domain.entities.task import Task

if TYPE_CHECKING:
    from domain.repositories.task_repository import TaskRepository
    from domain.services.holiday_checker import IHolidayChecker


class TaskAllocatorBase(ABC):
    """Abstract base class for task allocation strategies.

    Allocators are responsible for determining when and how to schedule
    a single task given current resource constraints.

    Each allocator implements a specific scheduling algorithm (greedy,
    balanced, backward, etc.) while the sorting of tasks is handled
    separately by the optimization strategy.
    """

    def __init__(
        self,
        default_start_hour: int,
        default_end_hour: int,
        holiday_checker: "IHolidayChecker | None" = None,
        current_time: datetime | None = None,
    ):
        """Initialize allocator with configuration.

        Args:
            default_start_hour: Default start hour for tasks (e.g., 9)
            default_end_hour: Default end hour for tasks (e.g., 18)
            holiday_checker: Optional IHolidayChecker for holiday detection
            current_time: Current time for calculating remaining hours on today
        """
        self.default_start_hour = default_start_hour
        self.default_end_hour = default_end_hour
        self.holiday_checker = holiday_checker
        self.current_time = current_time

    @abstractmethod
    def allocate(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
        daily_allocations: dict[date, float],
        repository: "TaskRepository",
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
        if task_copy.estimated_duration is None:
            raise ValueError("Cannot allocate task without estimated duration")
        return task_copy

    def _get_effective_deadline(self, task: Task) -> datetime | None:
        """Get effective deadline for task scheduling.

        Args:
            task: Task to get deadline for

        Returns:
            Effective deadline datetime, or None if no deadline
        """
        return task.deadline

    def _prepare_task_for_allocation(self, task: Task) -> tuple[Task, datetime | None] | None:
        """Validate and prepare task for allocation.

        This method combines common preparation steps used by all allocators:
        1. Validate task has estimated_duration
        2. Create a deep copy for modification
        3. Get effective deadline

        Args:
            task: Task to prepare

        Returns:
            Tuple of (task_copy, effective_deadline) if validation succeeds,
            None if validation fails
        """
        # Validate task
        if not self._validate_task(task):
            return None

        # Create copy and get deadline
        task_copy = self._create_task_copy(task)
        effective_deadline = self._get_effective_deadline(task_copy)

        return (task_copy, effective_deadline)

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

    def _get_current_allocation(
        self, daily_allocations: dict[date, float], date_obj: date
    ) -> float:
        """Get current allocation for a specific date.

        Args:
            daily_allocations: Current daily allocations
            date_obj: Date to look up

        Returns:
            Current allocation hours for the date
        """
        return daily_allocations.get(date_obj, 0.0)

    def _calculate_available_hours(
        self, daily_allocations: dict[date, float], date_obj: date, max_hours_per_day: float
    ) -> float:
        """Calculate available hours for a specific date.

        If the date is today and current_time is set, calculates remaining hours
        until end of business day (default_end_hour).

        Args:
            daily_allocations: Current daily allocations
            date_obj: Date to check
            max_hours_per_day: Maximum hours per day

        Returns:
            Available hours for the date
        """
        current_allocation = self._get_current_allocation(daily_allocations, date_obj)
        available_from_max = max_hours_per_day - current_allocation

        # If current_time is set and date_obj is today, limit by remaining hours
        if self.current_time and date_obj == self.current_time.date():
            end_hour = self.default_end_hour
            current_hour = self.current_time.hour + self.current_time.minute / 60.0
            remaining_hours_today = max(0.0, end_hour - current_hour)
            # Return minimum of available_from_max and remaining_hours_today
            return min(available_from_max, remaining_hours_today)

        return available_from_max

    def _set_planned_times(
        self,
        task: Task,
        schedule_start: datetime,
        schedule_end: datetime,
        task_daily_allocations: dict[date, float],
    ) -> None:
        """Set planned start, end, and daily allocations on task.

        Args:
            task: Task to update
            schedule_start: Start datetime
            schedule_end: End datetime
            task_daily_allocations: Daily allocation hours
        """
        # Set start time to default_start_hour (default: 9:00)
        start_date_with_time = schedule_start.replace(
            hour=self.default_start_hour, minute=0, second=0
        )
        task.planned_start = start_date_with_time

        # Set end time to default_end_hour (default: 18:00)
        end_date_with_time = schedule_end.replace(hour=self.default_end_hour, minute=0, second=0)
        task.planned_end = end_date_with_time
        task.daily_allocations = task_daily_allocations

    def _rollback_allocations(
        self, daily_allocations: dict[date, float], task_allocations: dict[date, float]
    ) -> None:
        """Rollback allocations from daily_allocations.

        Args:
            daily_allocations: Global daily allocations to rollback
            task_allocations: Task-specific allocations to remove
        """
        for date_obj, hours in task_allocations.items():
            daily_allocations[date_obj] -= hours
