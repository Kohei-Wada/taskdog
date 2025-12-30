"""Backward optimization strategy implementation."""

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from taskdog_core.application.dto.optimization_output import SchedulingFailure
from taskdog_core.application.services.optimization.allocation_context import (
    AllocationContext,
)
from taskdog_core.application.services.optimization.allocation_helpers import (
    calculate_available_hours,
    prepare_task_for_allocation,
    set_planned_times,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.services.optimization.sequential_allocation import (
    allocate_tasks_sequentially,
)
from taskdog_core.application.utils.date_helper import is_workday
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.application.dto.optimize_schedule_input import (
        OptimizeScheduleInput,
    )
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class BackwardOptimizationStrategy(OptimizationStrategy):
    """Backward (Just-In-Time) algorithm for task scheduling optimization.

    This strategy schedules tasks as late as possible while meeting deadlines:
    1. Sort tasks by deadline (furthest deadline first)
    2. For each task, allocate time blocks backward from deadline
    3. Fill time slots from deadline backwards
    """

    DISPLAY_NAME = "Backward"
    DESCRIPTION = "Just-in-time from deadlines"

    def __init__(self, default_start_hour: int, default_end_hour: int):
        self.default_start_hour = default_start_hour
        self.default_end_hour = default_end_hour

    def optimize_tasks(
        self,
        schedulable_tasks: list[Task],
        all_tasks_for_context: list[Task],
        input_dto: "OptimizeScheduleInput",
        holiday_checker: "IHolidayChecker | None" = None,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using backward allocation."""
        return allocate_tasks_sequentially(
            schedulable_tasks=schedulable_tasks,
            all_tasks_for_context=all_tasks_for_context,
            input_dto=input_dto,
            allocate_single_task=lambda task, ctx: self._allocate_task(
                task, ctx, holiday_checker
            ),
            sort_tasks=self._sort_tasks,
            holiday_checker=holiday_checker,
            workload_calculator=workload_calculator,
        )

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
        context: AllocationContext,
        holiday_checker: "IHolidayChecker | None" = None,
    ) -> Task | None:
        """Allocate task using backward allocation from deadline."""
        task_copy = prepare_task_for_allocation(task)
        if task_copy is None:
            return None

        effective_deadline = task_copy.deadline
        assert task_copy.estimated_duration is not None

        target_end = effective_deadline or context.start_date + timedelta(days=7)

        current_date = target_end
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        temp_allocations: list[tuple[date, float, datetime]] = []

        while remaining_hours > 0:
            if not is_workday(current_date, holiday_checker):
                current_date -= timedelta(days=1)
                continue

            if current_date < context.start_date:
                return None

            date_obj = current_date.date()
            available_hours = calculate_available_hours(
                context.daily_allocations,
                date_obj,
                context.max_hours_per_day,
                context.current_time,
                self.default_end_hour,
            )

            if available_hours > 0:
                allocated = min(remaining_hours, available_hours)
                temp_allocations.append((date_obj, allocated, current_date))
                remaining_hours -= allocated

            current_date -= timedelta(days=1)

        task_daily_allocations: dict[date, float] = {}
        for date_obj, hours, datetime_obj in reversed(temp_allocations):
            current_allocation = context.daily_allocations.get(date_obj, 0.0)
            context.daily_allocations[date_obj] = current_allocation + hours
            task_daily_allocations[date_obj] = hours

            if schedule_start is None:
                schedule_start = datetime_obj
            schedule_end = datetime_obj

        if schedule_start and schedule_end:
            start_with_time = schedule_start.replace(
                hour=self.default_start_hour, minute=0, second=0
            )
            set_planned_times(
                task_copy,
                start_with_time,
                schedule_end,
                task_daily_allocations,
                self.default_start_hour,
                self.default_end_hour,
            )
            return task_copy

        return None
