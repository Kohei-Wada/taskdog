"""Greedy optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.schedule_optimizer import ScheduleOptimizer
from domain.entities.task import Task


class GreedyOptimizationStrategy(OptimizationStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Sort tasks by priority (deadline urgency, priority field, hierarchy)
    2. Allocate time blocks sequentially in priority order
    3. Fill available time slots from start_date onwards

    This is a wrapper around the existing ScheduleOptimizer implementation.
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
        # Use the existing ScheduleOptimizer implementation
        optimizer = ScheduleOptimizer(
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            force_override=force_override,
        )

        # Run optimization
        modified_tasks = optimizer.optimize_tasks(tasks, repository)

        # Return modified tasks and daily allocations
        return modified_tasks, optimizer.allocator.daily_allocations
