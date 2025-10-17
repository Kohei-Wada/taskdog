"""Abstract base class for optimization strategies using Template Method Pattern."""

from abc import ABC, abstractmethod
from datetime import datetime

from application.services.task_filter import TaskFilter
from application.services.workload_allocator import WorkloadAllocator
from domain.entities.task import Task


class OptimizationStrategy(ABC):
    """Abstract base class for task scheduling optimization strategies.

    This class implements the Template Method pattern to eliminate code duplication
    across optimization strategies.

    The template method `optimize_tasks()` defines the common workflow:
    1. Initialize services (allocator, filter)
    2. Initialize existing allocations
    3. Filter schedulable tasks
    4. Sort tasks by priority (strategy-specific)
    5. Allocate tasks (strategy-specific)
    6. Return results

    Subclasses only need to implement sorting and allocation logic.
    """

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using template method pattern.

        This method defines the common workflow for all optimization strategies.
        Subclasses customize behavior by implementing abstract methods.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules

        Returns:
            Tuple of (modified_tasks, daily_allocations)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date strings to allocated hours
        """
        # 1. Initialize service instances (common for all strategies)
        allocator = WorkloadAllocator(max_hours_per_day, start_date, repository)
        task_filter = TaskFilter()

        # 2. Initialize daily_allocations with existing scheduled tasks
        allocator.initialize_allocations(tasks, force_override)

        # 3. Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        # 4. Sort tasks by strategy-specific priority
        sorted_tasks = self._sort_schedulable_tasks(schedulable_tasks, start_date, repository)

        # 5. Allocate time blocks for each task (strategy-specific)
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = self._allocate_task(task, allocator, start_date, max_hours_per_day)
            if updated_task:
                updated_tasks.append(updated_task)

        # 6. Return modified tasks and daily allocations
        return updated_tasks, allocator.daily_allocations

    @abstractmethod
    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by strategy-specific priority.

        Subclasses must implement this to define their sorting logic.

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Sorted task list
        """
        pass

    @abstractmethod
    def _allocate_task(
        self,
        task: Task,
        allocator: WorkloadAllocator,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block for a single task.

        Subclasses must implement this to define their allocation logic.

        Args:
            task: Task to schedule
            allocator: Workload allocator (for tracking daily_allocations)
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        pass
