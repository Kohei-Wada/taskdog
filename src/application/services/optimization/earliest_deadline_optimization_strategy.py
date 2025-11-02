"""Earliest Deadline First (EDF) optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.allocator_based_strategy import AllocatorBasedStrategy
from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from domain.entities.task import Task


class EarliestDeadlineOptimizationStrategy(AllocatorBasedStrategy):
    """Earliest Deadline First (EDF) algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on deadline proximity:
    1. Sort tasks by deadline (earliest first)
    2. Tasks without deadlines are scheduled last
    3. Allocate time blocks sequentially in deadline order using greedy allocation
    4. Ignore priority field completely

    The allocation uses greedy forward allocation, filling each day to maximum
    capacity before moving to the next day.
    """

    DISPLAY_NAME = "Earliest Deadline"
    DESCRIPTION = "EDF algorithm"

    def _get_allocator_class(self) -> type[TaskAllocatorBase]:
        """Return GreedyForwardAllocator for this strategy.

        Returns:
            GreedyForwardAllocator class for front-loading tasks
        """
        return GreedyForwardAllocator

    def _sort_schedulable_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by deadline (earliest first).

        Tasks are sorted by deadline in ascending order
        (earliest deadline = scheduled first). Tasks without deadlines
        are scheduled last (treated as infinite deadline).

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization

        Returns:
            Tasks sorted by deadline (earliest deadline first)
        """
        return sorted(
            tasks,
            key=lambda t: t.deadline
            if t.deadline is not None
            else datetime(9999, 12, 31, 23, 59, 59),
        )
