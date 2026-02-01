"""Balanced optimization strategy implementation."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from taskdog_core.application.constants.optimization import SCHEDULING_EPSILON
from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.application.services.optimization.allocation_helpers import (
    calculate_available_hours,
    prepare_task_for_allocation,
    set_planned_times,
)
from taskdog_core.application.services.optimization.greedy_based_optimization_strategy import (
    initialize_allocations,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.sorters.optimization_task_sorter import (
    OptimizationTaskSorter,
)
from taskdog_core.application.utils.date_helper import is_workday
from taskdog_core.domain.entities.task import Task
from taskdog_core.shared.constants import DEFAULT_SCHEDULE_DAYS
from taskdog_core.shared.utils.date_utils import count_weekdays


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

    def __init__(self, default_start_time: time, default_end_time: time):
        self.default_start_time = default_start_time
        self.default_end_time = default_end_time

    def optimize_tasks(
        self,
        tasks: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
    ) -> OptimizeResult:
        """Optimize task schedules using balanced distribution."""
        daily_allocations = initialize_allocations(context_tasks)
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
        """Sort tasks by priority (default sorting)."""
        sorter = OptimizationTaskSorter(start_date)
        return sorter.sort_by_priority(tasks)

    def _allocate_task(
        self,
        task: Task,
        daily_allocations: dict[date, float],
        params: OptimizeParams,
    ) -> Task | None:
        """Allocate task using balanced distribution with multi-pass approach."""
        task_copy = prepare_task_for_allocation(task)
        if task_copy is None:
            return None

        effective_deadline = task_copy.deadline
        assert task_copy.estimated_duration is not None

        end_date = effective_deadline or params.start_date + timedelta(
            days=DEFAULT_SCHEDULE_DAYS
        )

        available_weekdays = count_weekdays(params.start_date, end_date)
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
                state, daily_allocations, params, end_date, target_hours_per_day
            )
            if not made_progress:
                break

        if state.remaining_hours > SCHEDULING_EPSILON:
            for date_obj, hours in state.task_daily_allocations.items():
                daily_allocations[date_obj] -= hours
            return None

        if state.schedule_start and state.task_daily_allocations:
            # Calculate actual schedule_end from daily_allocations
            # This is necessary because multi-pass allocation may not update
            # schedule_end correctly when holidays are involved
            actual_schedule_end = datetime.combine(
                max(state.task_daily_allocations.keys()),
                state.schedule_start.time(),
            )
            set_planned_times(
                task_copy,
                state.schedule_start,
                actual_schedule_end,
                state.task_daily_allocations,
                self.default_start_time,
                self.default_end_time,
            )
            return task_copy

        return None

    def _allocate_single_pass(
        self,
        state: _AllocationState,
        daily_allocations: dict[date, float],
        params: OptimizeParams,
        end_date: datetime,
        target_hours_per_day: float,
    ) -> bool:
        """Execute single allocation pass across all days. Returns True if progress."""
        made_progress = False
        current_date = params.start_date

        while current_date <= end_date:
            if not params.include_all_days and not is_workday(
                current_date, params.holiday_checker
            ):
                current_date += timedelta(days=1)
                continue

            allocated = self._try_allocate_day(
                state, daily_allocations, params, current_date, target_hours_per_day
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
        daily_allocations: dict[date, float],
        params: OptimizeParams,
        current_date: datetime,
        target_hours_per_day: float,
    ) -> bool:
        """Try to allocate hours for a single day. Returns True if allocated."""
        date_obj = current_date.date()
        desired_allocation = min(target_hours_per_day, state.remaining_hours)

        available_hours = calculate_available_hours(
            daily_allocations,
            date_obj,
            params.max_hours_per_day,
            params.current_time,
            self.default_end_time,
        )

        if available_hours <= SCHEDULING_EPSILON:
            return False

        if state.schedule_start is None:
            state.schedule_start = current_date

        allocated = min(desired_allocation, available_hours)
        current_allocation = daily_allocations.get(date_obj, 0.0)
        daily_allocations[date_obj] = current_allocation + allocated
        state.task_daily_allocations[date_obj] = (
            state.task_daily_allocations.get(date_obj, 0.0) + allocated
        )
        state.remaining_hours -= allocated
        state.schedule_end = current_date
        return True
