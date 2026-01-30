"""Sequential allocation logic for optimization strategies."""

from collections.abc import Callable
from datetime import date, datetime
from typing import TYPE_CHECKING

from taskdog_core.application.dto.optimize_params import OptimizeParams
from taskdog_core.application.dto.optimize_result import OptimizeResult
from taskdog_core.application.sorters.optimization_task_sorter import (
    OptimizationTaskSorter,
)
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator

# Type alias for task allocator function
# Takes (task, daily_allocations, params) and returns updated task or None
TaskAllocator = Callable[[Task, dict[date, float], OptimizeParams], Task | None]


def allocate_tasks_sequentially(
    tasks: list[Task],
    context_tasks: list[Task],
    params: OptimizeParams,
    allocate_single_task: TaskAllocator,
    sort_tasks: Callable[[list[Task], datetime], list[Task]] | None = None,
    workload_calculator: "WorkloadCalculator | None" = None,
) -> OptimizeResult:
    """Allocate tasks sequentially using the provided allocation function.

    This function implements the common workflow for sequential optimization:
    1. Initialize daily allocations from context tasks
    2. Sort tasks (optional, uses default if not provided)
    3. Allocate each task using the provided allocator
    4. Return results

    Args:
        tasks: List of tasks to schedule
        context_tasks: All tasks for calculating existing allocations
        params: Optimization parameters (start_date, max_hours_per_day, etc.)
        allocate_single_task: Function to allocate a single task
        sort_tasks: Optional function to sort tasks (default: priority-based)
        workload_calculator: Optional pre-configured calculator

    Returns:
        OptimizeResult containing modified tasks, daily allocations, and failures
    """
    # Initialize daily allocations from existing tasks
    daily_allocations = _initialize_allocations(context_tasks, workload_calculator)
    result = OptimizeResult(daily_allocations=daily_allocations)

    if sort_tasks:
        sorted_tasks = sort_tasks(tasks, params.start_date)
    else:
        sorted_tasks = default_sort_tasks(tasks, params.start_date)

    for task in sorted_tasks:
        updated_task = allocate_single_task(task, daily_allocations, params)
        if updated_task:
            result.tasks.append(updated_task)
        else:
            result.record_allocation_failure(task)

    return result


def _initialize_allocations(
    tasks: list[Task],
    workload_calculator: "WorkloadCalculator | None" = None,
) -> dict[date, float]:
    """Initialize daily allocations from existing scheduled tasks.

    Args:
        tasks: Tasks to include in workload calculation (already filtered by caller)
        workload_calculator: Optional WorkloadCalculator for calculating task daily hours

    Returns:
        Dictionary mapping dates to allocated hours
    """
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator

    calculator = workload_calculator or WorkloadCalculator()
    daily_allocations: dict[date, float] = {}

    for task in tasks:
        # Skip tasks without schedules
        if not (task.planned_start and task.estimated_duration):
            continue

        # Get daily allocations for this task
        # Use task.daily_allocations if available, otherwise calculate from WorkloadCalculator
        task_daily_hours = task.daily_allocations or calculator.get_task_daily_hours(
            task
        )

        # Add to global daily_allocations
        for date_obj, hours in task_daily_hours.items():
            daily_allocations[date_obj] = daily_allocations.get(date_obj, 0.0) + hours

    return daily_allocations


def default_sort_tasks(tasks: list[Task], start_date: datetime) -> list[Task]:
    """Default task sorting by priority.

    Args:
        tasks: Tasks to sort
        start_date: Starting date for schedule optimization

    Returns:
        Sorted task list (highest priority first)
    """
    sorter = OptimizationTaskSorter(start_date)
    return sorter.sort_by_priority(tasks)
