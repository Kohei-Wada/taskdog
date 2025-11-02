"""Base class for optimization strategies that use allocators.

This module provides AllocatorBasedStrategy, a specialized base class for
optimization strategies that delegate allocation logic to TaskAllocator instances.
"""

from abc import abstractmethod
from typing import TYPE_CHECKING

from application.services.optimization.allocation_context import AllocationContext
from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task

if TYPE_CHECKING:
    pass


class AllocatorBasedStrategy(OptimizationStrategy):
    """Base class for strategies that use TaskAllocator for allocation logic.

    This class eliminates code duplication for simple strategies that:
    1. Use a specific TaskAllocator implementation (Greedy/Balanced/Backward)
    2. Optionally override sorting logic
    3. Don't need custom allocation logic beyond what allocators provide

    Subclasses only need to:
    - Implement `_get_allocator_class()` to specify which allocator to use
    - Optionally override `_sort_schedulable_tasks()` for custom sorting

    Benefits:
    - Reduces code duplication across simple strategies
    - Improves allocator reuse (created once, reused for all tasks)
    - Makes strategy differences (allocator type, sorting) explicit
    - Easier to add new strategies (just specify allocator and sorting)

    Example:
        class MyStrategy(AllocatorBasedStrategy):
            def _get_allocator_class(self):
                return GreedyForwardAllocator

            # Optional: custom sorting
            def _sort_schedulable_tasks(self, tasks, start_date):
                return sorted(tasks, key=lambda t: t.priority)
    """

    def __init__(self, default_start_hour: int, default_end_hour: int) -> None:
        """Initialize the allocator-based strategy.

        Args:
            default_start_hour: Default start hour for tasks (e.g., 9)
            default_end_hour: Default end hour for tasks (e.g., 18)
        """
        self.default_start_hour = default_start_hour
        self.default_end_hour = default_end_hour
        self._allocator: TaskAllocatorBase | None = None  # Lazy initialization

    @abstractmethod
    def _get_allocator_class(self) -> type[TaskAllocatorBase]:
        """Return the allocator class to use for this strategy.

        Subclasses must implement this to specify which TaskAllocator
        implementation (GreedyForwardAllocator, BalancedAllocator, etc.)
        should be used for task allocation.

        Returns:
            TaskAllocator class (not instance) to use for allocation

        Example:
            def _get_allocator_class(self):
                return GreedyForwardAllocator
        """

    def _allocate_task(
        self,
        task: Task,
        context: AllocationContext,
    ) -> Task | None:
        """Allocate time block for a task using the configured allocator.

        This method implements the allocation logic by delegating to a
        TaskAllocator instance. The allocator is created lazily on first
        use and reused for all subsequent tasks (performance optimization).

        Args:
            task: Task to schedule
            context: Allocation context with all necessary state

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        # Lazy initialization: create allocator on first use
        if self._allocator is None:
            allocator_class = self._get_allocator_class()
            self._allocator = allocator_class(
                default_start_hour=self.default_start_hour,
                default_end_hour=self.default_end_hour,
                holiday_checker=context.holiday_checker,
                current_time=context.current_time,
            )

        # Delegate allocation to the allocator
        return self._allocator.allocate(
            task=task,
            start_date=context.start_date,
            max_hours_per_day=context.max_hours_per_day,
            daily_allocations=context.daily_allocations,
            repository=context.repository,
        )
