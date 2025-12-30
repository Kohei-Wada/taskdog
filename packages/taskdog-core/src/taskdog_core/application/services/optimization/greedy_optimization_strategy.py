"""Greedy optimization strategy implementation."""

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

if TYPE_CHECKING:
    from taskdog_core.application.dto.optimize_schedule_input import (
        OptimizeScheduleInput,
    )
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


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

    def __init__(self, default_start_hour: int, default_end_hour: int):
        """Initialize strategy with configuration.

        Args:
            default_start_hour: Default start hour for tasks (e.g., 9)
            default_end_hour: Default end hour for tasks (e.g., 18)
        """
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
        """Optimize task schedules using greedy forward allocation.

        Args:
            schedulable_tasks: List of tasks to schedule
            all_tasks_for_context: All tasks for calculating existing allocations
            input_dto: Optimization parameters (start_date, max_hours_per_day, etc.)
            holiday_checker: Optional HolidayChecker for holiday detection
            workload_calculator: Optional pre-configured calculator

        Returns:
            Tuple of (modified_tasks, daily_allocations, failed_tasks)
        """
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
            holiday_checker: Optional holiday checker

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        task_copy = prepare_task_for_allocation(task)
        if task_copy is None:
            return None

        effective_deadline = task_copy.deadline

        current_date = context.start_date
        remaining_hours = task_copy.estimated_duration
        assert remaining_hours is not None
        schedule_start = None
        schedule_end = None
        task_daily_allocations: dict[date, float] = {}

        while remaining_hours > 0:
            if not is_workday(current_date, holiday_checker):
                current_date += timedelta(days=1)
                continue

            if effective_deadline and current_date > effective_deadline:
                rollback_allocations(context.daily_allocations, task_daily_allocations)
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
                if schedule_start is None:
                    schedule_start = current_date

                allocated = min(remaining_hours, available_hours)
                current_allocation = context.daily_allocations.get(date_obj, 0.0)
                context.daily_allocations[date_obj] = current_allocation + allocated
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
                self.default_start_hour,
                self.default_end_hour,
            )
            return task_copy

        rollback_allocations(context.daily_allocations, task_daily_allocations)
        return None
