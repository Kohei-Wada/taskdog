"""Abstract base class for optimization strategies using Template Method Pattern."""

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
    from taskdog_core.domain.repositories.task_repository import TaskRepository
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

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository: "TaskRepository",
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        holiday_checker: "IHolidayChecker | None" = None,
        current_time: datetime | None = None,
    ) -> tuple[list[Task], dict[date, float], list[SchedulingFailure]]:
        """Optimize task schedules using template method pattern.

        This method defines the common workflow for all optimization strategies.
        Subclasses customize behavior by implementing abstract methods.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            holiday_checker: Optional HolidayChecker for holiday detection
            current_time: Current time for calculating remaining hours on today

        Returns:
            Tuple of (modified_tasks, daily_allocations, failed_tasks)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date objects to allocated hours
            - failed_tasks: List of tasks that could not be scheduled with reasons
        """
        # 1. Create allocation context with initialized state
        context = AllocationContext.create(
            tasks=tasks,
            repository=repository,
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            force_override=force_override,
            holiday_checker=holiday_checker,
            current_time=current_time,
        )

        # 2. Filter tasks that need scheduling
        schedulable_tasks = [
            task for task in tasks if task.is_schedulable(force_override)
        ]

        # 3. Sort tasks by strategy-specific priority
        sorted_tasks = self._sort_schedulable_tasks(schedulable_tasks, start_date)

        # 4. Allocate time blocks for each task (strategy-specific)
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = self._allocate_task(task, context)
            if updated_task:
                updated_tasks.append(updated_task)
            else:
                # Record allocation failure with default reason
                context.record_allocation_failure(task)

        # 5. Return modified tasks, daily allocations, and failed tasks
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
        - context.repository: Task repository for hierarchy queries
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
