"""Balanced optimization strategy implementation."""

from datetime import date, timedelta

from taskdog_core.application.services.optimization.allocation_context import (
    AllocationContext,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.utils.date_helper import is_workday
from taskdog_core.domain.entities.task import Task
from taskdog_core.shared.constants import DEFAULT_SCHEDULE_DAYS
from taskdog_core.shared.utils.date_utils import count_weekdays


class BalancedOptimizationStrategy(OptimizationStrategy):
    """Balanced algorithm for task scheduling optimization.

    This strategy distributes workload evenly across the available time period:
    1. Sort tasks by priority (deadline urgency, priority field, task ID) - uses default sorting
    2. For each task, distribute hours evenly from start_date to deadline
    3. Respect max_hours_per_day constraint and weekday-only rule

    Benefits:
    - More realistic workload distribution
    - Prevents burnout by avoiding front-heavy scheduling
    - Better work-life balance

    Characteristics:
    - Even workload distribution (prevents front-loading)
    - Better work-life balance
    - Respects deadline constraints
    - Skips weekends
    - Defaults to 2-week period if no deadline
    """

    DISPLAY_NAME = "Balanced"
    DESCRIPTION = "Even workload distribution"

    def _allocate_task(self, task: Task, context: AllocationContext) -> Task | None:
        """Allocate task using balanced distribution.

        Distributes hours evenly across available weekdays from start_date
        to deadline (or 2 weeks if no deadline).

        Args:
            task: Task to schedule
            context: Allocation context with all necessary state

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        # Validate and prepare task
        task_copy = self._prepare_task_for_allocation(task)
        if task_copy is None:
            return None

        effective_deadline = task_copy.deadline
        assert (
            task_copy.estimated_duration is not None
        )  # Guaranteed by _prepare_task_for_allocation

        # Calculate end date for distribution
        # If no deadline, use a reasonable period (2 weeks = 10 weekdays)
        # DEFAULT_SCHEDULE_DAYS (13) days from start gives us ~2 weeks of weekdays
        end_date = effective_deadline or context.start_date + timedelta(
            days=DEFAULT_SCHEDULE_DAYS
        )

        # Calculate available weekdays in the period
        available_weekdays = count_weekdays(context.start_date, end_date)

        if available_weekdays == 0:
            return None

        # Calculate target hours per day (even distribution)
        target_hours_per_day = task_copy.estimated_duration / available_weekdays

        # Try to allocate with balanced distribution
        current_date = context.start_date
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        task_daily_allocations: dict[date, float] = {}

        while remaining_hours > 0 and current_date <= end_date:
            # Skip weekends and holidays
            if not is_workday(current_date, context.holiday_checker):
                current_date += timedelta(days=1)
                continue

            date_obj = current_date.date()

            # Calculate how much we want to allocate today (balanced approach)
            desired_allocation = min(target_hours_per_day, remaining_hours)

            # Check available hours considering max_hours_per_day constraint
            available_hours = self._calculate_available_hours(
                context.daily_allocations,
                date_obj,
                context.max_hours_per_day,
                context.current_time,
            )

            if available_hours > 0:
                # Record start date on first allocation
                if schedule_start is None:
                    schedule_start = current_date

                # Allocate as much as possible (up to desired amount)
                allocated = min(desired_allocation, available_hours)
                current_allocation = context.daily_allocations.get(date_obj, 0.0)
                context.daily_allocations[date_obj] = current_allocation + allocated
                task_daily_allocations[date_obj] = allocated
                remaining_hours -= allocated

                # Update end date
                schedule_end = current_date

            current_date += timedelta(days=1)

        # Check if we couldn't allocate all hours
        if remaining_hours > 0:
            # Rollback allocations and return None
            self._rollback_allocations(
                context.daily_allocations, task_daily_allocations
            )
            return None

        # Set planned times
        if schedule_start and schedule_end:
            self._set_planned_times(
                task_copy, schedule_start, schedule_end, task_daily_allocations
            )
            return task_copy

        return None
