"""Backward optimization strategy implementation."""

from datetime import date, datetime, timedelta

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.application.services.optimization.allocation_helpers import (
    SCHEDULE_START_TIME,
    calculate_available_hours,
    prepare_task_for_allocation,
    set_planned_times,
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
    """

    DISPLAY_NAME = "Backward"
    DESCRIPTION = "Just-in-time from deadlines"

    def optimize_tasks(
        self,
        tasks: list[Task],
        existing_allocations: dict[date, float],
        params: OptimizeParams,
    ) -> OptimizeResult:
        """Optimize task schedules using backward allocation."""
        # Copy existing allocations to avoid mutating the input
        daily_allocations = dict(existing_allocations)
        result = OptimizeResult(daily_allocations=daily_allocations)

        sorted_tasks = self._sort_tasks(tasks, params.start_date)

        for task in sorted_tasks:
            updated_task = self._allocate_task(task, daily_allocations, params)
            if updated_task:
                result.tasks.append(updated_task)
            else:
                result.record_allocation_failure(task)

        return result

    def _sort_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by deadline (furthest first)."""

        def deadline_key(task: Task) -> tuple[int, int, int | None]:
            if task.deadline:
                days_until = (task.deadline - start_date).days
                return (0, -days_until, task.id)
            else:
                return (1, 0, task.id)

        return sorted(tasks, key=deadline_key)

    def _allocate_task(
        self,
        task: Task,
        daily_allocations: dict[date, float],
        params: OptimizeParams,
    ) -> Task | None:
        """Allocate task using backward allocation from deadline."""
        task_copy = prepare_task_for_allocation(task)
        if task_copy is None:
            return None

        effective_deadline = task_copy.deadline
        assert task_copy.estimated_duration is not None

        target_end = effective_deadline or params.start_date + timedelta(days=7)

        current_date = target_end
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        temp_allocations: list[tuple[date, float, datetime]] = []

        while remaining_hours > 0:
            if not params.include_all_days and not is_workday(
                current_date, params.holiday_checker
            ):
                current_date -= timedelta(days=1)
                continue

            if current_date < params.start_date:
                return None

            date_obj = current_date.date()
            available_hours = calculate_available_hours(
                daily_allocations,
                date_obj,
                params.max_hours_per_day,
                params.current_time,
            )

            if available_hours > 0:
                allocated = min(remaining_hours, available_hours)
                temp_allocations.append((date_obj, allocated, current_date))
                remaining_hours -= allocated

            current_date -= timedelta(days=1)

        task_daily_allocations: dict[date, float] = {}
        for date_obj, hours, datetime_obj in reversed(temp_allocations):
            current_allocation = daily_allocations.get(date_obj, 0.0)
            daily_allocations[date_obj] = current_allocation + hours
            task_daily_allocations[date_obj] = hours

            if schedule_start is None:
                schedule_start = datetime_obj
            schedule_end = datetime_obj

        if schedule_start and schedule_end:
            start_with_time = schedule_start.replace(
                hour=SCHEDULE_START_TIME.hour,
                minute=SCHEDULE_START_TIME.minute,
                second=SCHEDULE_START_TIME.second,
            )
            set_planned_times(
                task_copy,
                start_with_time,
                schedule_end,
                task_daily_allocations,
            )
            return task_copy

        return None
