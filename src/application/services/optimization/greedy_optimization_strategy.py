"""Greedy optimization strategy implementation."""

import copy
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from application.services.optimization.allocation_context import AllocationContext
from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.utils.date_helper import is_workday
from domain.entities.task import Task

if TYPE_CHECKING:
    pass


class GreedyOptimizationStrategy(OptimizationStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Sort tasks by priority (deadline urgency, priority field, task ID) - uses default sorting
    2. Allocate time blocks sequentially in priority order
    3. Fill available time slots from start_date onwards (greedy forward allocation)

    The greedy allocation fills each day to its maximum capacity before
    moving to the next day, prioritizing early completion.
    """

    DISPLAY_NAME = "Greedy"
    DESCRIPTION = "Front-loads tasks (default)"

    def __init__(self, default_start_hour: int, default_end_hour: int):
        """Initialize strategy with configuration.

        Args:
            default_start_hour: Default start hour for tasks (e.g., 9)
            default_end_hour: Default end hour for tasks (e.g., 18)
        """
        self.default_start_hour = default_start_hour
        self.default_end_hour = default_end_hour

    def _allocate_task(self, task: Task, context: AllocationContext) -> Task | None:
        """Allocate task using greedy forward allocation.

        Finds the earliest available time slot that satisfies:
        - Starts on or after start_date
        - Respects max_hours_per_day constraint
        - Allocates across weekdays only
        - Fills each day greedily (maximum possible hours per day)
        - Completes before effective deadline

        Args:
            task: Task to schedule
            context: Allocation context with all necessary state

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        # Validate and prepare task
        if not task.estimated_duration or task.estimated_duration <= 0:
            return None

        task_copy = copy.deepcopy(task)
        if task_copy.estimated_duration is None:
            raise ValueError("Cannot allocate task without estimated duration")
        effective_deadline = task_copy.deadline

        # Find earliest available start date
        current_date = context.start_date
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        task_daily_allocations: dict[date, float] = {}

        while remaining_hours > 0:
            # Skip weekends and holidays
            if not is_workday(current_date, context.holiday_checker):
                current_date += timedelta(days=1)
                continue

            # Check deadline constraint
            if effective_deadline and current_date > effective_deadline:
                # Cannot schedule before deadline - rollback
                self._rollback_allocations(context.daily_allocations, task_daily_allocations)
                return None

            # Get available hours for this day
            date_obj = current_date.date()
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

                # Allocate as much as possible for this day (greedy approach)
                allocated = min(remaining_hours, available_hours)
                current_allocation = context.daily_allocations.get(date_obj, 0.0)
                context.daily_allocations[date_obj] = current_allocation + allocated
                task_daily_allocations[date_obj] = allocated
                remaining_hours -= allocated

                # Update end date
                schedule_end = current_date

            current_date += timedelta(days=1)

        # Set planned times
        if schedule_start and schedule_end:
            self._set_planned_times(task_copy, schedule_start, schedule_end, task_daily_allocations)
            return task_copy

        # Failed to allocate - rollback
        self._rollback_allocations(context.daily_allocations, task_daily_allocations)
        return None

    def _calculate_available_hours(
        self,
        daily_allocations: dict[date, float],
        date_obj: date,
        max_hours_per_day: float,
        current_time: datetime | None,
    ) -> float:
        """Calculate available hours for a specific date.

        If the date is today and current_time is set, calculates remaining hours
        until end of business day.

        Args:
            daily_allocations: Current daily allocations
            date_obj: Date to check
            max_hours_per_day: Maximum hours per day
            current_time: Current time for today's calculation

        Returns:
            Available hours for the date
        """
        current_allocation = daily_allocations.get(date_obj, 0.0)
        available_from_max = max_hours_per_day - current_allocation

        # If current_time is set and date_obj is today, limit by remaining hours
        if current_time and date_obj == current_time.date():
            end_hour = self.default_end_hour
            current_hour = current_time.hour + current_time.minute / 60.0
            remaining_hours_today = max(0.0, end_hour - current_hour)
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
        task.set_daily_allocations(task_daily_allocations)

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
