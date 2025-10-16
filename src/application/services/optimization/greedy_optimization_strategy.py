"""Greedy optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.task_filter import TaskFilter
from application.services.workload_allocator import WorkloadAllocator
from application.sorters.optimization_task_sorter import OptimizationTaskSorter
from domain.entities.task import Task


class GreedyOptimizationStrategy(OptimizationStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Filter schedulable tasks (has estimated_duration, not completed/in_progress)
    2. Sort tasks by priority (deadline urgency, priority field, hierarchy)
    3. Allocate time blocks sequentially in priority order
    4. Fill available time slots from start_date onwards
    5. Update parent task periods based on children
    """

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using greedy algorithm.

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
        # Initialize service instances
        allocator = WorkloadAllocator(max_hours_per_day, start_date, repository)
        task_filter = TaskFilter()
        sorter = OptimizationTaskSorter(start_date, repository)

        # Initialize daily_allocations with existing scheduled tasks
        # This ensures we account for tasks that won't be rescheduled
        allocator.initialize_allocations(tasks, force_override)

        # Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        # Sort by priority
        sorted_tasks = sorter.sort_by_priority(schedulable_tasks)

        # Allocate time blocks for each task
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = allocator.allocate_timeblock(task)
            if updated_task:
                updated_tasks.append(updated_task)

        # Return modified tasks and daily allocations
        return updated_tasks, allocator.daily_allocations
