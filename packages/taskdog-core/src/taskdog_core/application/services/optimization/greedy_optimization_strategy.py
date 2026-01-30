"""Greedy optimization strategy implementation."""

from datetime import date, time, timedelta
from typing import TYPE_CHECKING

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
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

if TYPE_CHECKING:
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator


class GreedyOptimizationStrategy(OptimizationStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Sort tasks by priority (deadline urgency, priority field, task ID)
    2. Allocate time blocks sequentially in priority order
    3. Fill available time slots from start_date onwards (greedy forward allocation)

    The greedy allocation fills each day to its maximum capacity before
    moving to the next day, prioritizing early completion.
    """

    DISPLAY_NAME = "Greedy"
    DESCRIPTION = "Front-loads tasks"

    def __init__(self, default_start_time: time, default_end_time: time):
        """Initialize strategy with configuration.

        Args:
            default_start_time: Default start time for tasks (e.g., time(9, 0))
            default_end_time: Default end time for tasks (e.g., time(18, 0))
        """
        self.default_start_time = default_start_time
        self.default_end_time = default_end_time

    def optimize_tasks(
        self,
        tasks: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> OptimizeResult:
        """Optimize task schedules using greedy forward allocation.

        Args:
            tasks: List of tasks to schedule
            context_tasks: All tasks for calculating existing allocations
            params: Optimization parameters (start_date, max_hours_per_day, etc.)
            workload_calculator: Optional pre-configured calculator

        Returns:
            OptimizeResult containing modified tasks, daily allocations, and failures
        """
        return allocate_tasks_sequentially(
            tasks=tasks,
            context_tasks=context_tasks,
            params=params,
            allocate_single_task=lambda task, daily_alloc, p: self._allocate_task(
                task, daily_alloc, p
            ),
            workload_calculator=workload_calculator,
        )

    def _allocate_task(
        self,
        task: Task,
        daily_allocations: dict[date, float],
        params: OptimizeParams,
    ) -> Task | None:
        """Allocate task using greedy forward allocation.

        Finds the earliest available time slot that satisfies:
        - Starts on or after start_date
        - Respects max_hours_per_day constraint
        - Allocates across weekdays only
        - Fills each day greedily (maximum possible hours per day)
        - Completes before effective deadline

        Args:
            task: Task to schedule
            daily_allocations: Current daily allocations (modified in place)
            params: Optimization parameters

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        task_copy = prepare_task_for_allocation(task)
        if task_copy is None:
            return None

        effective_deadline = task_copy.deadline

        current_date = params.start_date
        remaining_hours = task_copy.estimated_duration
        assert remaining_hours is not None
        schedule_start = None
        schedule_end = None
        task_daily_allocations: dict[date, float] = {}

        while remaining_hours > 0:
            if not is_workday(current_date, params.holiday_checker):
                current_date += timedelta(days=1)
                continue

            if effective_deadline and current_date > effective_deadline:
                rollback_allocations(daily_allocations, task_daily_allocations)
                return None

            date_obj = current_date.date()
            available_hours = calculate_available_hours(
                daily_allocations,
                date_obj,
                params.max_hours_per_day,
                params.current_time,
                self.default_end_time,
            )

            if available_hours > 0:
                if schedule_start is None:
                    schedule_start = current_date

                allocated = min(remaining_hours, available_hours)
                current_allocation = daily_allocations.get(date_obj, 0.0)
                daily_allocations[date_obj] = current_allocation + allocated
                task_daily_allocations[date_obj] = allocated
                remaining_hours -= allocated

                schedule_end = current_date

            current_date += timedelta(days=1)

        if schedule_start and schedule_end:
            set_planned_times(
                task_copy,
                schedule_start,
                schedule_end,
                task_daily_allocations,
                self.default_start_time,
                self.default_end_time,
            )
            return task_copy

        rollback_allocations(daily_allocations, task_daily_allocations)
        return None
