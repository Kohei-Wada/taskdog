"""Dependency-aware optimization strategy implementation using Critical Path Method."""

from datetime import datetime

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.task_filter import TaskFilter
from application.services.workload_allocator import WorkloadAllocator
from domain.entities.task import Task


class DependencyAwareOptimizationStrategy(OptimizationStrategy):
    """Dependency-aware algorithm using Critical Path Method (CPM).

    This strategy schedules tasks while respecting parent-child dependencies:
    1. Filter schedulable tasks (has estimated_duration, not completed/in_progress)
    2. Calculate dependency depth for each task (children are scheduled before parents)
    3. Sort by dependency depth (leaf tasks first, then their parents)
    4. Within same depth, use priority and deadline as secondary sort
    5. Allocate time blocks respecting the dependency order
    6. Update parent task periods based on children automatically
    """

    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using dependency-aware algorithm.

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

        # Initialize daily_allocations with existing scheduled tasks
        allocator.initialize_allocations(tasks, force_override)

        # Filter tasks that need scheduling
        schedulable_tasks = task_filter.get_schedulable_tasks(tasks, force_override)

        # Calculate dependency depth for each task
        task_depths = self._calculate_dependency_depths(schedulable_tasks, repository)

        # Sort by dependency depth (leaf tasks first), then by priority/deadline
        sorted_tasks = sorted(
            schedulable_tasks,
            key=lambda t: (
                task_depths.get(
                    t.id if t.id is not None else 0, 0
                ),  # Lower depth = scheduled first
                # Secondary sort: deadline urgency
                (t.deadline if t.deadline else "9999-12-31 23:59:59"),
                # Tertiary sort: priority (higher = scheduled first, so negate)
                -(t.priority if t.priority is not None else 0),
            ),
        )

        # Allocate time blocks for each task
        updated_tasks = []
        for task in sorted_tasks:
            updated_task = allocator.allocate_timeblock(task)
            if updated_task:
                updated_tasks.append(updated_task)

        # Update parent task periods based on children
        # Schedule propagation removed (no parent-child hierarchy)

        # Return modified tasks and daily allocations
        return updated_tasks, allocator.daily_allocations

    def _calculate_dependency_depths(self, tasks: list[Task], repository) -> dict[int, int]:
        """Calculate dependency depth for each task.

        Since parent-child relationships have been removed, all tasks have depth 0.

        Args:
            tasks: List of tasks to analyze
            repository: Task repository (unused, kept for compatibility)

        Returns:
            Dict mapping task_id to dependency depth (always 0)
        """
        # All tasks have depth 0 now (no hierarchy)
        return {task.id: 0 for task in tasks if task.id is not None}
