"""Greedy optimization strategy implementation."""

import copy
from datetime import date, timedelta
from typing import TYPE_CHECKING

from taskdog_core.application.services.optimization.allocation_context import (
    AllocationContext,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.utils.date_helper import is_workday
from taskdog_core.domain.entities.task import Task

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
                self._rollback_allocations(
                    context.daily_allocations, task_daily_allocations
                )
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
            self._set_planned_times(
                task_copy, schedule_start, schedule_end, task_daily_allocations
            )
            return task_copy

        # Failed to allocate - rollback
        self._rollback_allocations(context.daily_allocations, task_daily_allocations)
        return None
