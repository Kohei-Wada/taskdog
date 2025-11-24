"""Dependency-aware optimization strategy implementation using Critical Path Method."""

from datetime import datetime

from taskdog_core.application.services.optimization.greedy_optimization_strategy import (
    GreedyOptimizationStrategy,
)
from taskdog_core.domain.entities.task import Task


class DependencyAwareOptimizationStrategy(GreedyOptimizationStrategy):
    """Deadline and priority-based optimization strategy.

    This strategy schedules tasks by deadline urgency and priority:
    1. Sort tasks by deadline (earlier deadlines first)
    2. Secondary sort by priority (higher priority first)
    3. Allocate time blocks using greedy forward allocation

    Note: Despite the name "Dependency Aware", this strategy currently only
    considers deadline and priority. Parent-child relationships were removed
    from the task model. The name is kept for backward compatibility.

    The allocation uses greedy forward allocation (inherited from GreedyOptimizationStrategy),
    filling each day to maximum capacity before moving to the next day.
    """

    DISPLAY_NAME = "Dependency Aware"
    DESCRIPTION = "Deadline + Priority"

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime
    ) -> list[Task]:
        """Sort tasks by deadline and priority.

        Since parent-child relationships were removed, this strategy now
        sorts by deadline urgency and priority only.

        Sort criteria:
        - Primary: Deadline (earlier deadline = scheduled first)
        - Secondary: Priority (higher priority = scheduled first)

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization

        Returns:
            Tasks sorted by deadline and priority
        """
        # Sort by deadline (earlier first), then by priority (higher first)
        return sorted(
            tasks,
            key=lambda t: (
                # Primary sort: deadline urgency (earlier = scheduled first)
                (t.deadline if t.deadline else datetime(9999, 12, 31, 23, 59, 59)),
                # Secondary sort: priority (higher = scheduled first, so negate)
                -(t.priority if t.priority is not None else 0),
            ),
        )
