"""Base class for optimization strategies that use allocators.

This module provides AllocatorBasedStrategy, a specialized base class for
optimization strategies that delegate allocation logic to TaskAllocator instances.
"""

from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task
from shared.config_manager import Config

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

    def __init__(self, config: Config) -> None:
        """Initialize the allocator-based strategy.

        Args:
            config: Configuration object for strategy settings
        """
        self.config = config
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
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block for a task using the configured allocator.

        This method implements the allocation logic by delegating to a
        TaskAllocator instance. The allocator is created lazily on first
        use and reused for all subsequent tasks (performance optimization).

        Args:
            task: Task to schedule
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        # Lazy initialization: create allocator on first use
        if self._allocator is None:
            allocator_class = self._get_allocator_class()
            self._allocator = allocator_class(
                config=self.config,
                holiday_checker=self.holiday_checker,
                current_time=self.current_time,
            )

        # Delegate allocation to the allocator
        return self._allocator.allocate(
            task=task,
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            daily_allocations=self.daily_allocations,
            repository=self.repository,
        )
