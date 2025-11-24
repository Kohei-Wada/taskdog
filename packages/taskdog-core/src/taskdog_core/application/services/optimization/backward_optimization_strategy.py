"""Backward optimization strategy implementation."""

import copy
from datetime import date, datetime, timedelta

from taskdog_core.application.services.optimization.allocation_context import (
    AllocationContext,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.utils.date_helper import is_workday
from taskdog_core.domain.entities.task import Task


class BackwardOptimizationStrategy(OptimizationStrategy):
    """Backward (Just-In-Time) algorithm for task scheduling optimization.

    This strategy schedules tasks as late as possible while meeting deadlines:
    1. Sort tasks by deadline (furthest deadline first)
    2. For each task, allocate time blocks backward from deadline
    3. Fill time slots from deadline backwards

    Benefits:
    - Maximum flexibility for requirement changes
    - Prevents early resource commitment
    - Just-In-Time delivery approach
    - Keeps options open longer

    Characteristics:
    - Just-In-Time delivery approach
    - Maximum flexibility for requirement changes
    - Prevents early resource commitment
    - Respects deadline constraints
    - Skips weekends
    - Defaults to 1-week period if no deadline
    """

    DISPLAY_NAME = "Backward"
    DESCRIPTION = "Just-in-time from deadlines"

    def _allocate_task(self, task: Task, context: AllocationContext) -> Task | None:
        """Allocate task using backward allocation from deadline.

        Schedules the task as late as possible, working backward from the
        deadline to find available time slots.

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

        # Determine the target end date
        # If no deadline, schedule in near future (e.g., 1 week from start)
        target_end = effective_deadline or context.start_date + timedelta(days=7)

        # Allocate backward from target_end
        current_date = target_end
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None

        # Collect allocations in reverse order
        temp_allocations: list[tuple[date, float, datetime]] = []

        while remaining_hours > 0:
            # Skip weekends and holidays
            if not is_workday(current_date, context.holiday_checker):
                current_date -= timedelta(days=1)
                continue

            # Don't go before start_date
            if current_date < context.start_date:
                # Cannot schedule - insufficient time before deadline
                return None

            date_obj = current_date.date()

            # Calculate available hours for this day
            available_hours = self._calculate_available_hours(
                context.daily_allocations,
                date_obj,
                context.max_hours_per_day,
                context.current_time,
            )

            if available_hours > 0:
                # Allocate as much as possible for this day
                allocated = min(remaining_hours, available_hours)
                temp_allocations.append((date_obj, allocated, current_date))
                remaining_hours -= allocated

            current_date -= timedelta(days=1)

        # Apply allocations (we collected them in reverse, so apply in correct order)
        task_daily_allocations = {}
        for date_obj, hours, datetime_obj in reversed(temp_allocations):
            current_allocation = context.daily_allocations.get(date_obj, 0.0)
            context.daily_allocations[date_obj] = current_allocation + hours
            task_daily_allocations[date_obj] = hours

            # Track start and end
            if schedule_start is None:
                schedule_start = datetime_obj
            schedule_end = datetime_obj

        # Set planned times
        if schedule_start and schedule_end:
            # Use start_date's time for schedule_start
            start_with_time = schedule_start.replace(
                hour=context.start_date.hour,
                minute=context.start_date.minute,
                second=context.start_date.second,
            )
            self._set_planned_times(
                task_copy, start_with_time, schedule_end, task_daily_allocations
            )
            return task_copy

        return None

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime
    ) -> list[Task]:
        """Sort tasks by deadline (furthest first).

        Tasks without deadlines are placed at the beginning
        (they will be scheduled first = furthest from now).

        Args:
            tasks: Tasks to sort
            start_date: Reference date for deadline calculation

        Returns:
            Sorted task list (furthest deadline first)
        """

        def deadline_key(task: Task) -> tuple[int, int, int | None]:
            if task.deadline:
                deadline_dt = task.deadline
                days_until = (deadline_dt - start_date).days
                # Negative to get furthest first
                return (0, -days_until, task.id)
            else:
                # Tasks without deadline: schedule first (no deadline pressure)
                return (1, 0, task.id)

        return sorted(tasks, key=deadline_key)
