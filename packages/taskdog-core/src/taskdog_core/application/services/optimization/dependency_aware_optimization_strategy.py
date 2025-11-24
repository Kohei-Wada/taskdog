"""Dependency-aware optimization strategy implementation using Critical Path Method."""

from datetime import datetime

from taskdog_core.application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from taskdog_core.domain.entities.task import Task


class DependencyAwareOptimizationStrategy(GreedyOptimizationStrategy):
    """Critical Path Method (CPM) optimization strategy.

    This strategy schedules tasks based on their position in the dependency graph,
    prioritizing tasks that block other tasks (critical path tasks):

    1. Calculate blocking count: How many tasks depend on each task
    2. Sort by blocking count (higher = schedule first)
    3. Secondary sort by deadline (earlier first)
    4. Tertiary sort by priority (higher first)
    5. Allocate time blocks using greedy forward allocation

    Benefits:
    - Bottleneck tasks are scheduled first, unblocking dependent tasks
    - Minimizes overall project duration by addressing critical path
    - Tasks with no dependencies are scheduled last (maximum flexibility)

    The allocation uses greedy forward allocation (inherited from GreedyOptimizationStrategy),
    filling each day to maximum capacity before moving to the next day.

    Note: This strategy respects task.depends_on relationships to identify
    critical path tasks.
    """

    DISPLAY_NAME = "Dependency Aware"
    DESCRIPTION = "Critical Path Method"

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime
    ) -> list[Task]:
        """Sort tasks using Critical Path Method (CPM).

        Schedule tasks that block other tasks first to minimize overall project
        duration. This implementation uses blocking count as the primary sort key.

        Sort criteria:
        - Primary: Blocking count (tasks that block more others = scheduled first)
        - Secondary: Deadline (earlier deadline = scheduled first)
        - Tertiary: Priority (higher priority = scheduled first)

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization

        Returns:
            Tasks sorted by critical path priority (blocking tasks first)
        """
        # Build blocking count map: how many tasks depend on each task
        blocking_count: dict[int, int] = {}
        for task in tasks:
            if task.id is not None:
                blocking_count[task.id] = 0

        # Count how many tasks are blocked by each task
        for task in tasks:
            for dep_id in task.depends_on:
                if dep_id in blocking_count:
                    blocking_count[dep_id] += 1

        def critical_path_key(task: Task) -> tuple[int, datetime, int]:
            """Sort key for critical path scheduling."""
            task_id = task.id if task.id is not None else 0
            blocking = blocking_count.get(task_id, 0)
            deadline_val = (
                task.deadline if task.deadline else datetime(9999, 12, 31, 23, 59, 59)
            )
            priority_val = task.priority if task.priority is not None else 0

            return (
                -blocking,  # Higher blocking count = schedule first (descending)
                deadline_val,  # Earlier deadline = schedule first (ascending)
                -priority_val,  # Higher priority = schedule first (descending)
            )

        return sorted(tasks, key=critical_path_key)
