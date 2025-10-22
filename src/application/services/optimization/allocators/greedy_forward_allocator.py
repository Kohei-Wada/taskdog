"""Greedy forward allocation strategy implementation."""

from datetime import datetime, timedelta

from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task
from shared.utils.date_utils import is_workday


class GreedyForwardAllocator(TaskAllocatorBase):
    """Greedy forward allocation algorithm.

    This allocator schedules tasks as early as possible, filling each
    day to its maximum capacity before moving to the next day.

    Characteristics:
    - Front-loads work (completes tasks as soon as possible)
    - Fills each day to max_hours_per_day before moving to next day
    - Respects deadline constraints
    - Skips weekends
    """

    def allocate(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
        daily_allocations: dict[str, float],
        repository,
    ) -> Task | None:
        """Allocate task using greedy forward allocation.

        Finds the earliest available time slot that satisfies:
        - Starts on or after start_date
        - Respects max_hours_per_day constraint
        - Allocates across weekdays only
        - Fills each day greedily (maximum possible hours per day)
        - Completes before effective deadline

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
        if not self._validate_task(task):
            return None

        task_copy = self._create_task_copy(task)
        effective_deadline = self._get_effective_deadline(task_copy)

        # Find earliest available start date
        current_date = start_date
        remaining_hours = task_copy.estimated_duration  # Type narrowed by _create_task_copy
        assert remaining_hours is not None  # For mypy
        schedule_start = None
        schedule_end = None
        task_daily_allocations: dict[str, float] = {}

        while remaining_hours > 0:
            # Skip weekends and holidays
            if not is_workday(current_date, self.holiday_checker):
                current_date += timedelta(days=1)
                continue

            # Check deadline constraint
            if effective_deadline:
                deadline_dt = datetime.strptime(effective_deadline, DATETIME_FORMAT)
                if current_date > deadline_dt:
                    # Cannot schedule before deadline - rollback
                    self._rollback_allocations(daily_allocations, task_daily_allocations)
                    return None

            # Get available hours for this day
            date_str = self._get_date_str(current_date)
            available_hours = self._calculate_available_hours(
                daily_allocations, date_str, max_hours_per_day
            )

            if available_hours > 0:
                # Record start date on first allocation
                if schedule_start is None:
                    schedule_start = current_date

                # Allocate as much as possible for this day (greedy approach)
                allocated = min(remaining_hours, available_hours)
                current_allocation = self._get_current_allocation(daily_allocations, date_str)
                daily_allocations[date_str] = current_allocation + allocated
                task_daily_allocations[date_str] = allocated
                remaining_hours -= allocated

                # Update end date
                schedule_end = current_date

            current_date += timedelta(days=1)

        # Set planned times
        if schedule_start and schedule_end:
            self._set_planned_times(task_copy, schedule_start, schedule_end, task_daily_allocations)
            return task_copy

        # Failed to allocate - rollback
        self._rollback_allocations(daily_allocations, task_daily_allocations)
        return None
