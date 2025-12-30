"""Sequential allocation logic for optimization strategies."""

from collections.abc import Callable
from datetime import date, datetime
from typing import TYPE_CHECKING

from taskdog_core.application.dto.optimization_output import SchedulingFailure
from taskdog_core.application.services.optimization.allocation_context import (
    AllocationContext,
)
from taskdog_core.application.sorters.optimization_task_sorter import (
    OptimizationTaskSorter,
)
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.application.dto.optimize_schedule_input import (
        OptimizeScheduleInput,
    )
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker

# Type alias for task allocator function
TaskAllocator = Callable[[Task, AllocationContext], Task | None]


def allocate_tasks_sequentially(
    schedulable_tasks: list[Task],
    all_tasks_for_context: list[Task],
    input_dto: "OptimizeScheduleInput",
    allocate_single_task: TaskAllocator,
    sort_tasks: Callable[[list[Task], datetime], list[Task]] | None = None,
    holiday_checker: "IHolidayChecker | None" = None,
    workload_calculator: "WorkloadCalculator | None" = None,
) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
    """Allocate tasks sequentially using the provided allocation function.

    This function implements the common workflow for sequential optimization:
    1. Create allocation context
    2. Sort tasks (optional, uses default if not provided)
    3. Allocate each task using the provided allocator
    4. Return results

    Args:
        schedulable_tasks: List of tasks to schedule
        all_tasks_for_context: All tasks for calculating existing allocations
        input_dto: Optimization parameters (start_date, max_hours_per_day, etc.)
        allocate_single_task: Function to allocate a single task
        sort_tasks: Optional function to sort tasks (default: priority-based)
        holiday_checker: Optional HolidayChecker for holiday detection
        workload_calculator: Optional pre-configured calculator

    Returns:
        Tuple of (modified_tasks, daily_allocations, failed_tasks)
    """
    context = AllocationContext.create(
        tasks=all_tasks_for_context,
        start_date=input_dto.start_date,
        max_hours_per_day=input_dto.max_hours_per_day,
        holiday_checker=holiday_checker,
        current_time=input_dto.current_time,
        workload_calculator=workload_calculator,
    )

    if sort_tasks:
        sorted_tasks = sort_tasks(schedulable_tasks, input_dto.start_date)
    else:
        sorted_tasks = default_sort_tasks(schedulable_tasks, input_dto.start_date)

    updated_tasks = []
    for task in sorted_tasks:
        updated_task = allocate_single_task(task, context)
        if updated_task:
            updated_tasks.append(updated_task)
        else:
            context.record_allocation_failure(task)

    return updated_tasks, context.daily_allocations, context.failed_tasks


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
