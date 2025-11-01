"""Balanced allocation strategy implementation."""

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.repositories.task_repository import TaskRepository

from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from domain.entities.task import Task
from shared.constants import DEFAULT_SCHEDULE_DAYS
from shared.utils.date_utils import count_weekdays, is_workday


class BalancedAllocator(TaskAllocatorBase):
    """Balanced allocation algorithm.

    This allocator distributes task hours evenly across the available
    time period, aiming for consistent daily workload.

    Characteristics:
    - Even workload distribution (prevents front-loading)
    - Better work-life balance
    - Respects deadline constraints
    - Skips weekends
    - Defaults to 2-week period if no deadline
    """

    def allocate(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
        daily_allocations: dict[date, float],
        repository: "TaskRepository",
    ) -> Task | None:
        """Allocate task using balanced distribution.

        Distributes hours evenly across available weekdays from start_date
        to deadline (or 2 weeks if no deadline).

        Args:
            task: Task to schedule
            start_date: Earliest allowed start date
            max_hours_per_day: Maximum hours per day
            daily_allocations: Current daily allocations (will be modified)
            repository: Task repository for deadline calculations

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        # Validate and prepare task
        prepared = self._prepare_task_for_allocation(task)
        if prepared is None:
            return None
        task_copy, effective_deadline = prepared

        # Calculate end date for distribution
        # If no deadline, use a reasonable period (2 weeks = 10 weekdays)
        # DEFAULT_SCHEDULE_DAYS (13) days from start gives us ~2 weeks of weekdays
        end_date = effective_deadline or start_date + timedelta(days=DEFAULT_SCHEDULE_DAYS)

        # Calculate available weekdays in the period
        available_weekdays = count_weekdays(start_date, end_date)

        if available_weekdays == 0:
            return None

        # Type narrowing for estimated_duration
        estimated_duration = task_copy.estimated_duration
        if estimated_duration is None:
            raise ValueError("Estimated duration cannot be None for balanced allocation")

        # Calculate target hours per day (even distribution)
        target_hours_per_day = estimated_duration / available_weekdays

        # Try to allocate with balanced distribution
        current_date = start_date
        remaining_hours = estimated_duration
        schedule_start = None
        schedule_end = None
        task_daily_allocations: dict[date, float] = {}

        while remaining_hours > 0 and current_date <= end_date:
            # Skip weekends and holidays
            if not is_workday(current_date, self.holiday_checker):
                current_date += timedelta(days=1)
                continue

            date_obj = current_date.date()

            # Calculate how much we want to allocate today (balanced approach)
            desired_allocation = min(target_hours_per_day, remaining_hours)

            # Check available hours considering max_hours_per_day constraint
            available_hours = self._calculate_available_hours(
                daily_allocations, date_obj, max_hours_per_day
            )

            if available_hours > 0:
                # Record start date on first allocation
                if schedule_start is None:
                    schedule_start = current_date

                # Allocate as much as possible (up to desired amount)
                allocated = min(desired_allocation, available_hours)
                current_allocation = self._get_current_allocation(daily_allocations, date_obj)
                daily_allocations[date_obj] = current_allocation + allocated
                task_daily_allocations[date_obj] = allocated
                remaining_hours -= allocated

                # Update end date
                schedule_end = current_date

            current_date += timedelta(days=1)

        # Check if we couldn't allocate all hours
        if remaining_hours > 0:
            # Rollback allocations and return None
            self._rollback_allocations(daily_allocations, task_daily_allocations)
            return None

        # Set planned times
        if schedule_start and schedule_end:
            self._set_planned_times(task_copy, schedule_start, schedule_end, task_daily_allocations)
            return task_copy

        return None
