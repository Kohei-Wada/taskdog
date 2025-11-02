"""Balanced optimization strategy implementation."""

from application.services.optimization.allocator_based_strategy import AllocatorBasedStrategy
from application.services.optimization.allocators.balanced_allocator import (
    BalancedAllocator,
)
from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase


class BalancedOptimizationStrategy(AllocatorBasedStrategy):
    """Balanced algorithm for task scheduling optimization.

    This strategy distributes workload evenly across the available time period:
    1. Sort tasks by priority (deadline urgency, priority field, task ID) - uses default sorting
    2. For each task, distribute hours evenly from start_date to deadline
    3. Respect max_hours_per_day constraint and weekday-only rule

    Benefits:
    - More realistic workload distribution
    - Prevents burnout by avoiding front-heavy scheduling
    - Better work-life balance

    This class inherits common workflow from AllocatorBasedStrategy
    and only implements allocator selection.
    """

    DISPLAY_NAME = "Balanced"
    DESCRIPTION = "Even workload distribution"

    def _get_allocator_class(self) -> type[TaskAllocatorBase]:
        """Return BalancedAllocator for this strategy.

        Returns:
            BalancedAllocator class for even workload distribution
        """
        return BalancedAllocator
