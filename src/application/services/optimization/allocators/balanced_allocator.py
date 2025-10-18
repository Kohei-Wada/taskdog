"""Balanced allocation strategy implementation."""

import copy
from datetime import datetime, timedelta

from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from domain.constants import DATETIME_FORMAT
from domain.entities.task import Task
from domain.services.deadline_calculator import DeadlineCalculator
from shared.constants import DEFAULT_SCHEDULE_DAYS
from shared.workday_utils import WorkdayUtils


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

    def allocate(  # noqa: C901
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
        daily_allocations: dict[str, float],
        repository,
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
        if not task.estimated_duration:
            return None

        # Create a deep copy to avoid modifying the original task
        task_copy = copy.deepcopy(task)

        # Type narrowing: estimated_duration is guaranteed to be float at this point
        assert task_copy.estimated_duration is not None

        # Calculate effective deadline considering parent task deadlines
        effective_deadline = DeadlineCalculator.get_effective_deadline(task_copy, repository)

        # Calculate end date for distribution
        if effective_deadline:
            end_date = datetime.strptime(effective_deadline, DATETIME_FORMAT)
        else:
            # If no deadline, use a reasonable period (2 weeks = 10 weekdays)
            # DEFAULT_SCHEDULE_DAYS (13) days from start gives us ~2 weeks of weekdays
            end_date = start_date + timedelta(days=DEFAULT_SCHEDULE_DAYS)

        # Calculate available weekdays in the period
        available_weekdays = WorkdayUtils.count_weekdays(start_date, end_date)

        if available_weekdays == 0:
            return None

        # Calculate target hours per day (even distribution)
        target_hours_per_day = task_copy.estimated_duration / available_weekdays

        # Try to allocate with balanced distribution
        current_date = start_date
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        task_daily_allocations = {}

        while remaining_hours > 0 and current_date <= end_date:
            # Skip weekends
            if WorkdayUtils.is_weekend(current_date):
                current_date += timedelta(days=1)
                continue

            date_str = current_date.strftime("%Y-%m-%d")
            current_allocation = daily_allocations.get(date_str, 0.0)

            # Calculate how much we want to allocate today (balanced approach)
            desired_allocation = min(target_hours_per_day, remaining_hours)

            # Check available hours considering max_hours_per_day constraint
            available_hours = max_hours_per_day - current_allocation

            if available_hours > 0:
                # Record start date on first allocation
                if schedule_start is None:
                    schedule_start = current_date

                # Allocate as much as possible (up to desired amount)
                allocated = min(desired_allocation, available_hours)
                daily_allocations[date_str] = current_allocation + allocated
                task_daily_allocations[date_str] = allocated
                remaining_hours -= allocated

                # Update end date
                schedule_end = current_date

            current_date += timedelta(days=1)

        # Check if we couldn't allocate all hours
        if remaining_hours > 0:
            # Rollback allocations and return None
            for date_str, hours in task_daily_allocations.items():
                daily_allocations[date_str] -= hours
            return None

        # Set planned times
        if schedule_start and schedule_end:
            task_copy.planned_start = schedule_start.strftime(DATETIME_FORMAT)
            end_date_with_time = schedule_end.replace(
                hour=self.config.time.default_end_hour, minute=0, second=0
            )
            task_copy.planned_end = end_date_with_time.strftime(DATETIME_FORMAT)
            task_copy.daily_allocations = task_daily_allocations
            return task_copy

        return None
