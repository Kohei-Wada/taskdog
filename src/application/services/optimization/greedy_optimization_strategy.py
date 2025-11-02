"""Greedy optimization strategy implementation."""

from application.services.optimization.allocator_based_strategy import AllocatorBasedStrategy
from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase


class GreedyOptimizationStrategy(AllocatorBasedStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Sort tasks by priority (deadline urgency, priority field, task ID) - uses default sorting
    2. Allocate time blocks sequentially in priority order
    3. Fill available time slots from start_date onwards (greedy forward allocation)

    The greedy allocation fills each day to its maximum capacity before
    moving to the next day, prioritizing early completion.
    """

    DISPLAY_NAME = "Greedy"
    DESCRIPTION = "Front-loads tasks (default)"

    def _get_allocator_class(self) -> type[TaskAllocatorBase]:
        """Return GreedyForwardAllocator for this strategy.

        Returns:
            GreedyForwardAllocator class for front-loading tasks
        """
        return GreedyForwardAllocator
