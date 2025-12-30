"""Balanced optimization strategy implementation."""

from datetime import date, timedelta
from typing import TYPE_CHECKING

from taskdog_core.application.dto.optimization_output import SchedulingFailure
from taskdog_core.application.services.optimization.allocation_context import (
    AllocationContext,
)
from taskdog_core.application.services.optimization.allocation_helpers import (
    calculate_available_hours,
    prepare_task_for_allocation,
    rollback_allocations,
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
from taskdog_core.shared.constants import DEFAULT_SCHEDULE_DAYS
from taskdog_core.shared.utils.date_utils import count_weekdays

if TYPE_CHECKING:
    from taskdog_core.application.dto.optimize_schedule_input import (
        OptimizeScheduleInput,
    )
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class BalancedOptimizationStrategy(OptimizationStrategy):
    """Balanced algorithm for task scheduling optimization.

    This strategy distributes workload evenly across the available time period:
    1. Sort tasks by priority (deadline urgency, priority field, task ID)
    2. For each task, distribute hours evenly from start_date to deadline
    3. Respect max_hours_per_day constraint and weekday-only rule
    """

    DISPLAY_NAME = "Balanced"
    DESCRIPTION = "Even workload distribution"

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
        """Optimize task schedules using balanced distribution."""
        return allocate_tasks_sequentially(
            schedulable_tasks=schedulable_tasks,
            all_tasks_for_context=all_tasks_for_context,
            input_dto=input_dto,
            allocate_single_task=lambda task, ctx: self._allocate_task(
                task, ctx, holiday_checker
            ),
            holiday_checker=holiday_checker,
            workload_calculator=workload_calculator,
        )

    def _allocate_task(
        self,
        task: Task,
        context: AllocationContext,
        holiday_checker: "IHolidayChecker | None" = None,
    ) -> Task | None:
        """Allocate task using balanced distribution."""
        task_copy = prepare_task_for_allocation(task)
        if task_copy is None:
            return None

        effective_deadline = task_copy.deadline
        assert task_copy.estimated_duration is not None

        end_date = effective_deadline or context.start_date + timedelta(
            days=DEFAULT_SCHEDULE_DAYS
        )

        available_weekdays = count_weekdays(context.start_date, end_date)
        if available_weekdays == 0:
            return None

        target_hours_per_day = task_copy.estimated_duration / available_weekdays

        current_date = context.start_date
        remaining_hours = task_copy.estimated_duration
        schedule_start = None
        schedule_end = None
        task_daily_allocations: dict[date, float] = {}

        while remaining_hours > 0 and current_date <= end_date:
            if not is_workday(current_date, holiday_checker):
                current_date += timedelta(days=1)
                continue

            date_obj = current_date.date()
            desired_allocation = min(target_hours_per_day, remaining_hours)

            available_hours = calculate_available_hours(
                context.daily_allocations,
                date_obj,
                context.max_hours_per_day,
                context.current_time,
                self.default_end_hour,
            )

            if available_hours > 0:
                if schedule_start is None:
                    schedule_start = current_date

                allocated = min(desired_allocation, available_hours)
                current_allocation = context.daily_allocations.get(date_obj, 0.0)
                context.daily_allocations[date_obj] = current_allocation + allocated
                task_daily_allocations[date_obj] = allocated
                remaining_hours -= allocated
                schedule_end = current_date

            current_date += timedelta(days=1)

        if remaining_hours > 0:
            rollback_allocations(context.daily_allocations, task_daily_allocations)
            return None

        if schedule_start and schedule_end:
            set_planned_times(
                task_copy,
                schedule_start,
                schedule_end,
                task_daily_allocations,
                self.default_start_hour,
                self.default_end_hour,
            )
            return task_copy

        return None
