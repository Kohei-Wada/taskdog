"""Earliest Deadline First (EDF) optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.schedule_propagator import SchedulePropagator
from application.services.task_filter import TaskFilter
from application.services.workload_allocator import WorkloadAllocator
from domain.entities.task import Task


class EarliestDeadlineOptimizationStrategy(OptimizationStrategy):
    """Earliest Deadline First (EDF) algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on deadline proximity:
    1. Filter schedulable tasks (has estimated_duration, not completed/in_progress)
    2. Sort tasks by deadline (earliest first)
    3. Tasks without deadlines are scheduled last
    4. Allocate time blocks sequentially in deadline order
    5. Ignore priority field completely
    6. Update parent task periods based on children
    """

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using EDF algorithm.

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
        allocator = WorkloadAllocator(max_hours_per_day, start_date)
        task_filter = TaskFilter()
        schedule_propagator = SchedulePropagator(repository)

        # Initialize daily_allocations with existing scheduled tasks
        allocator.initialize_allocations(tasks, force_override)

        # Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        # Sort by deadline (earliest first)
        # Tasks without deadline go last (treated as infinite deadline)
        sorted_tasks = sorted(
            schedulable_tasks,
            key=lambda t: t.deadline if t.deadline is not None else datetime.max,
        )

        # Allocate time blocks for each task
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = allocator.allocate_timeblock(task)
            if updated_task:
                updated_tasks.append(updated_task)

        # Update parent task periods based on children
        all_tasks_with_updates = schedule_propagator.propagate_periods(tasks, updated_tasks)

        # If force_override, clear schedules for tasks that couldn't be scheduled
        if force_override:
            all_tasks_with_updates = schedule_propagator.clear_unscheduled_tasks(
                tasks, all_tasks_with_updates
            )

        # Return modified tasks and daily allocations
        return all_tasks_with_updates, allocator.daily_allocations
