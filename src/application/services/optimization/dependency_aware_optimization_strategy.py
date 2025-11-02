"""Dependency-aware optimization strategy implementation using Critical Path Method."""

from datetime import datetime

from application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from domain.entities.task import Task


class DependencyAwareOptimizationStrategy(GreedyOptimizationStrategy):
    """Dependency-aware algorithm using Critical Path Method (CPM).

    This strategy schedules tasks while respecting parent-child dependencies:
    1. Calculate dependency depth for each task (children are scheduled before parents)
    2. Sort by dependency depth (leaf tasks first, then their parents)
    3. Within same depth, use priority and deadline as secondary sort
    4. Allocate time blocks respecting the dependency order using greedy allocation

    The allocation uses greedy forward allocation (inherited from GreedyOptimizationStrategy),
    filling each day to maximum capacity before moving to the next day.
    """

    DISPLAY_NAME = "Dependency Aware"
    DESCRIPTION = "Critical Path Method"

    def _sort_schedulable_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by dependency depth, then by priority/deadline.

        Calculate dependency depth for each task and sort with multiple criteria:
        - Primary: Dependency depth (lower depth = scheduled first)
        - Secondary: Deadline (earlier deadline = scheduled first)
        - Tertiary: Priority (higher priority = scheduled first)

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization

        Returns:
            Tasks sorted by dependency depth, deadline, and priority
        """
        # Calculate dependency depth for each task
        task_depths = self._calculate_dependency_depths(tasks)

        # Sort by dependency depth (leaf tasks first), then by priority/deadline
        return sorted(
            tasks,
            key=lambda t: (
                task_depths.get(
                    t.id if t.id is not None else 0, 0
                ),  # Lower depth = scheduled first
                # Secondary sort: deadline urgency
                (t.deadline if t.deadline else datetime(9999, 12, 31, 23, 59, 59)),
                # Tertiary sort: priority (higher = scheduled first, so negate)
                -(t.priority if t.priority is not None else 0),
            ),
        )

    def _calculate_dependency_depths(self, tasks: list[Task]) -> dict[int, int]:
        """Calculate dependency depth for each task.

        Since parent-child relationships have been removed, all tasks have depth 0.

        Args:
            tasks: List of tasks to analyze

        Returns:
            Dict mapping task_id to dependency depth (always 0)
        """
        # All tasks have depth 0 now (no hierarchy)
        return {task.id: 0 for task in tasks if task.id is not None}
