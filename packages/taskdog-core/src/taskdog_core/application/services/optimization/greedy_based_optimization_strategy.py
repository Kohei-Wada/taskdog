"""Base class for greedy-based optimization strategies."""

from datetime import date, datetime, time, timedelta

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.application.services.optimization.allocation_helpers import (
    calculate_available_hours,
    prepare_task_for_allocation,
    set_planned_times,
)
from taskdog_core.application.services.optimization.optimization_strategy import (
    OptimizationStrategy,
)
from taskdog_core.application.sorters.optimization_task_sorter import (
    OptimizationTaskSorter,
)
from taskdog_core.application.utils.date_helper import is_workday
from taskdog_core.domain.entities.task import Task


class GreedyBasedOptimizationStrategy(OptimizationStrategy):
    """Base class for strategies that use greedy forward allocation.

    This class provides:
    1. Common workflow: initialize allocations → sort tasks → allocate each task
    2. Greedy forward allocation algorithm (_allocate_task)
    3. Daily allocation initialization from existing tasks

    Subclasses can customize behavior by overriding:
    - _sort_tasks(): Change task ordering (default: priority-based)
    """

    DISPLAY_NAME = "Greedy"
    DESCRIPTION = "Front-loads tasks"

    def __init__(self, default_start_time: time, default_end_time: time):
        """Initialize strategy with configuration.

        Args:
            default_start_time: Default start time for tasks (e.g., time(9, 0))
            default_end_time: Default end time for tasks (e.g., time(18, 0))
        """
        super().__init__()
        self.default_start_time = default_start_time
        self.default_end_time = default_end_time

    def optimize_tasks(
        self,
        tasks: list[Task],
        context_tasks: list[Task],
        params: OptimizeParams,
    ) -> OptimizeResult:
        """Optimize task schedules using greedy forward allocation.

        Args:
            tasks: List of tasks to schedule
            context_tasks: All tasks for calculating existing allocations
            params: Optimization parameters (start_date, max_hours_per_day, etc.)

        Returns:
            OptimizeResult containing modified tasks, daily allocations, and failures
        """
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
        """Sort tasks for allocation order.

        Default implementation: priority-based sorting (same as Greedy strategy).
        Subclasses can override for different sorting (deadline, dependencies, etc.).

        Args:
            tasks: Tasks to sort
            start_date: Starting date for schedule optimization

        Returns:
            Sorted task list
        """
        sorter = OptimizationTaskSorter(start_date)
        return sorter.sort_by_priority(tasks)

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
            if not params.include_all_days and not is_workday(
                current_date, params.holiday_checker
            ):
                current_date += timedelta(days=1)
                continue

            if effective_deadline and current_date > effective_deadline:
                for date_obj, hours in task_daily_allocations.items():
                    daily_allocations[date_obj] -= hours
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

        for date_obj, hours in task_daily_allocations.items():
            daily_allocations[date_obj] -= hours
        return None


def initialize_allocations(
    tasks: list[Task],
) -> dict[date, float]:
    """Initialize daily allocations from existing scheduled tasks.

    This function is also used by RoundRobinOptimizationStrategy and other
    strategies that need to account for existing task allocations.

    Args:
        tasks: Tasks to include in workload calculation (already filtered by caller)

    Returns:
        Dictionary mapping dates to allocated hours
    """
    daily_allocations: dict[date, float] = {}

    for task in tasks:
        # Skip tasks without schedules or daily_allocations
        if not (task.planned_start and task.daily_allocations):
            continue

        # Add task's daily allocations to global daily_allocations
        for date_obj, hours in task.daily_allocations.items():
            daily_allocations[date_obj] = daily_allocations.get(date_obj, 0.0) + hours

    return daily_allocations
