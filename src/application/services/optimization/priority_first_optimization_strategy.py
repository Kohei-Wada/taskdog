"""Priority-first optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.allocator_based_strategy import AllocatorBasedStrategy
from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from domain.entities.task import Task


class PriorityFirstOptimizationStrategy(AllocatorBasedStrategy):
    """Priority-first algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on priority field value:
    1. Sort tasks by priority field only (descending: higher priority first)
    2. Allocate time blocks sequentially in priority order using greedy allocation
    3. Ignore deadlines completely (focuses only on priority)

    The allocation uses greedy forward allocation, filling each day to maximum
    capacity before moving to the next day.
    """

    DISPLAY_NAME = "Priority First"
    DESCRIPTION = "Priority-based scheduling"

    def _get_allocator_class(self) -> type[TaskAllocatorBase]:
        """Return GreedyForwardAllocator for this strategy.

        Returns:
            GreedyForwardAllocator class for front-loading tasks
        """
        return GreedyForwardAllocator

    def _sort_schedulable_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by priority field only (priority-first approach).

        Tasks are sorted by priority value in descending order
        (higher priority = scheduled first). Tasks without priority go last.

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization

        Returns:
            Tasks sorted by priority (highest priority first)
        """
        return sorted(
            tasks,
            key=lambda t: t.priority if t.priority is not None else -1,
            reverse=True,
        )
