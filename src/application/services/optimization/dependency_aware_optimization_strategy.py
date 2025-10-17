"""Dependency-aware optimization strategy implementation using Critical Path Method."""

from datetime import datetime

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.workload_allocator import WorkloadAllocator
from domain.entities.task import Task


class DependencyAwareOptimizationStrategy(OptimizationStrategy):
    """Dependency-aware algorithm using Critical Path Method (CPM).

    This strategy schedules tasks while respecting parent-child dependencies:
    1. Calculate dependency depth for each task (children are scheduled before parents)
    2. Sort by dependency depth (leaf tasks first, then their parents)
    3. Within same depth, use priority and deadline as secondary sort
    4. Allocate time blocks respecting the dependency order

    This class inherits common workflow from OptimizationStrategy
    and only implements strategy-specific sorting and allocation logic.
    """

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by dependency depth, then by priority/deadline.

        Calculate dependency depth for each task and sort with multiple criteria:
        - Primary: Dependency depth (lower depth = scheduled first)
        - Secondary: Deadline (earlier deadline = scheduled first)
        - Tertiary: Priority (higher priority = scheduled first)

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Tasks sorted by dependency depth, deadline, and priority
        """
        # Calculate dependency depth for each task
        task_depths = self._calculate_dependency_depths(tasks, repository)

        # Sort by dependency depth (leaf tasks first), then by priority/deadline
        return sorted(
            tasks,
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

    def _allocate_task(
        self,
        task: Task,
        allocator: WorkloadAllocator,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block using greedy forward allocation.

        Uses WorkloadAllocator's standard greedy allocation which
        fills time slots from start_date onwards.

        Args:
            task: Task to schedule
            allocator: Workload allocator (for tracking daily_allocations)
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        return allocator.allocate_timeblock(task)

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
