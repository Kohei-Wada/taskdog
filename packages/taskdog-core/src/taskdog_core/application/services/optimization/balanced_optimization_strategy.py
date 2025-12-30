"""Balanced optimization strategy implementation."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from taskdog_core.application.constants.optimization import SCHEDULING_EPSILON
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


@dataclass
class _AllocationState:
    """Internal state for balanced allocation."""

    remaining_hours: float
    schedule_start: datetime | None
    schedule_end: datetime | None
    task_daily_allocations: dict[date, float]


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
        """Allocate task using balanced distribution with multi-pass approach."""
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
        state = _AllocationState(
            remaining_hours=task_copy.estimated_duration,
            schedule_start=None,
            schedule_end=None,
            task_daily_allocations={},
        )

        # Multi-pass allocation until all hours allocated or no capacity
        while state.remaining_hours > SCHEDULING_EPSILON:
            made_progress = self._allocate_single_pass(
                state, context, end_date, target_hours_per_day, holiday_checker
            )
            if not made_progress:
                break

        if state.remaining_hours > SCHEDULING_EPSILON:
            rollback_allocations(
                context.daily_allocations, state.task_daily_allocations
            )
            return None

        if state.schedule_start and state.schedule_end:
            set_planned_times(
                task_copy,
                state.schedule_start,
                state.schedule_end,
                state.task_daily_allocations,
                self.default_start_hour,
                self.default_end_hour,
            )
            return task_copy

        return None

    def _allocate_single_pass(
        self,
        state: _AllocationState,
        context: AllocationContext,
        end_date: datetime,
        target_hours_per_day: float,
        holiday_checker: "IHolidayChecker | None",
    ) -> bool:
        """Execute single allocation pass across all days. Returns True if progress."""
        made_progress = False
        current_date = context.start_date

        while current_date <= end_date:
            if not is_workday(current_date, holiday_checker):
                current_date += timedelta(days=1)
                continue

            allocated = self._try_allocate_day(
                state, context, current_date, target_hours_per_day
            )
            if allocated:
                made_progress = True
                if state.remaining_hours <= SCHEDULING_EPSILON:
                    break

            current_date += timedelta(days=1)

        return made_progress

    def _try_allocate_day(
        self,
        state: _AllocationState,
        context: AllocationContext,
        current_date: datetime,
        target_hours_per_day: float,
    ) -> bool:
        """Try to allocate hours for a single day. Returns True if allocated."""
        date_obj = current_date.date()
        desired_allocation = min(target_hours_per_day, state.remaining_hours)

        available_hours = calculate_available_hours(
            context.daily_allocations,
            date_obj,
            context.max_hours_per_day,
            context.current_time,
            self.default_end_hour,
        )

        if available_hours <= SCHEDULING_EPSILON:
            return False

        if state.schedule_start is None:
            state.schedule_start = current_date

        allocated = min(desired_allocation, available_hours)
        current_allocation = context.daily_allocations.get(date_obj, 0.0)
        context.daily_allocations[date_obj] = current_allocation + allocated
        state.task_daily_allocations[date_obj] = (
            state.task_daily_allocations.get(date_obj, 0.0) + allocated
        )
        state.remaining_hours -= allocated
        state.schedule_end = current_date
        return True
