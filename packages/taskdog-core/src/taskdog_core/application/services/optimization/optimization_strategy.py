"""Abstract base class for optimization strategies using Template Method Pattern."""

import copy
from abc import ABC, abstractmethod
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
    from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class OptimizationStrategy(ABC):
    """Abstract base class for task scheduling optimization strategies.

    This class implements the Template Method pattern to eliminate code duplication
    across optimization strategies.

    The template method `optimize_tasks()` defines the common workflow:
    1. Initialize context (repository, constraints, daily_allocations)
    2. Initialize existing allocations from scheduled tasks
    3. Filter schedulable tasks
    4. Sort tasks by priority (strategy-specific)
    5. Allocate tasks (strategy-specific)
    6. Return results

    Subclasses implement sorting and allocation logic specific to their algorithm.
    Each strategy has full control over its allocation algorithm.
    """

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
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        holiday_checker: "IHolidayChecker | None" = None,
        current_time: datetime | None = None,
        workload_calculator: "WorkloadCalculator | None" = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using template method pattern.

        This method defines the common workflow for all optimization strategies.
        Subclasses customize behavior by implementing abstract methods.

        Args:
            schedulable_tasks: List of tasks to schedule (already filtered by is_schedulable())
            all_tasks_for_context: All tasks in the system (for calculating existing allocations)
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            holiday_checker: Optional HolidayChecker for holiday detection
            current_time: Current time for calculating remaining hours on today
            workload_calculator: Optional pre-configured calculator for workload calculation

        Returns:
            Tuple of (modified_tasks, daily_allocations, failed_tasks)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date objects to allocated hours
            - failed_tasks: List of tasks that could not be scheduled with reasons
        """
        # 1. Create allocation context with initialized state
        # Pass workload_calculator from UseCase for proper strategy selection
        # NOTE: all_tasks_for_context should already be filtered by UseCase
        # to include only tasks that should count in workload calculation
        context = AllocationContext.create(
            tasks=all_tasks_for_context,
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            holiday_checker=holiday_checker,
            current_time=current_time,
            workload_calculator=workload_calculator,
        )

        # 2. Sort tasks by strategy-specific priority
        # No filtering needed - schedulable_tasks is already filtered by UseCase
        sorted_tasks = self._sort_schedulable_tasks(schedulable_tasks, start_date)

        # 3. Allocate time blocks for each task (strategy-specific)
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = self._allocate_task(task, context)
            if updated_task:
                updated_tasks.append(updated_task)
            else:
                # Record allocation failure with default reason
                context.record_allocation_failure(task)

        # 4. Return modified tasks, daily allocations, and failed tasks
        return updated_tasks, context.daily_allocations, context.failed_tasks

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime
    ) -> list[Task]:
        """Sort tasks by strategy-specific priority.

        Default implementation sorts by deadline urgency, priority field, and task ID.
        Strategies can override this method for custom sorting logic.

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization

        Returns:
            Sorted task list (highest priority first)
        """
        sorter = OptimizationTaskSorter(start_date)
        return sorter.sort_by_priority(tasks)

    @abstractmethod
    def _allocate_task(
        self,
        task: Task,
        context: AllocationContext,
    ) -> Task | None:
        """Allocate time block for a single task.

        Subclasses must implement this to define their allocation logic.
        The context provides access to:
        - context.daily_allocations: Current daily allocation state
        - context.start_date: Starting date for allocation
        - context.max_hours_per_day: Maximum hours per day constraint
        - context.holiday_checker: Holiday checker (optional)
        - context.current_time: Current time (optional)

        Args:
            task: Task to schedule
            context: Allocation context with all necessary state

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        pass

    def _prepare_task_for_allocation(self, task: Task) -> Task | None:
        """Validate and prepare task copy for allocation.

        Protected helper method that validates task duration and creates
        a deep copy for allocation. This eliminates code duplication across
        strategy implementations.

        Args:
            task: Task to validate and copy

        Returns:
            Deep copy of task if valid, None if task cannot be allocated
            (e.g., no estimated_duration or duration <= 0)

        Raises:
            ValueError: If deep copied task has None estimated_duration
                       (defensive check, should not happen in practice)
        """
        # Validate task has positive estimated duration
        if not task.estimated_duration or task.estimated_duration <= 0:
            return None

        # Create deep copy for modification
        task_copy = copy.deepcopy(task)

        # Defensive check: ensure copy preserved estimated_duration
        if task_copy.estimated_duration is None:
            raise ValueError("Cannot allocate task without estimated duration")

        return task_copy

    def _calculate_available_hours(
        self,
        daily_allocations: dict[date, float],
        date_obj: date,
        max_hours_per_day: float,
        current_time: datetime | None,
    ) -> float:
        """Calculate available hours for a specific date.

        Protected helper method available to all strategies.

        Args:
            daily_allocations: Current daily allocations
            date_obj: Date to check
            max_hours_per_day: Maximum work hours per day
            current_time: Optional current time for today's remaining hours

        Returns:
            Available hours (0.0 if fully allocated or past end hour)
        """
        current_allocation = daily_allocations.get(date_obj, 0.0)
        available_from_max = max_hours_per_day - current_allocation

        # If checking today, account for remaining hours
        if current_time and date_obj == current_time.date():
            end_hour = self.default_end_hour
            current_hour = current_time.hour + current_time.minute / 60.0
            remaining_hours_today = max(0.0, end_hour - current_hour)
            return min(available_from_max, remaining_hours_today)

        return available_from_max

    def _set_planned_times(
        self,
        task: Task,
        schedule_start: datetime,
        schedule_end: datetime,
        task_daily_allocations: dict[date, float],
    ) -> None:
        """Set planned start, end, and daily allocations on task.

        Protected helper method available to all strategies.

        Args:
            task: Task to update (modified in place)
            schedule_start: Start date of schedule
            schedule_end: End date of schedule
            task_daily_allocations: Daily hour allocations
        """
        # Set start time to default_start_hour (e.g., 9:00 AM)
        start_date_with_time = schedule_start.replace(
            hour=self.default_start_hour, minute=0, second=0
        )
        task.planned_start = start_date_with_time

        # Set end time to default_end_hour (e.g., 6:00 PM)
        end_date_with_time = schedule_end.replace(
            hour=self.default_end_hour, minute=0, second=0
        )
        task.planned_end = end_date_with_time

        # Set daily allocations
        task.set_daily_allocations(task_daily_allocations)

    def _rollback_allocations(
        self, daily_allocations: dict[date, float], task_allocations: dict[date, float]
    ) -> None:
        """Rollback allocations from daily_allocations.

        Protected helper method available to all strategies.
        Used when a task allocation fails and needs to be undone.

        Args:
            daily_allocations: Global daily allocations (modified in place)
            task_allocations: Task's allocations to roll back
        """
        for date_obj, hours in task_allocations.items():
            daily_allocations[date_obj] -= hours
