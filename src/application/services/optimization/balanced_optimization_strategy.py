"""Balanced optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.allocators.balanced_allocator import (
    BalancedAllocator,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task
from shared.config_manager import Config


class BalancedOptimizationStrategy(OptimizationStrategy):
    """Balanced algorithm for task scheduling optimization.

    This strategy distributes workload evenly across the available time period:
    1. Sort tasks by priority (deadline urgency, priority field, task ID) - uses default sorting
    2. For each task, distribute hours evenly from start_date to deadline
    3. Respect max_hours_per_day constraint and weekday-only rule

    Benefits:
    - More realistic workload distribution
    - Prevents burnout by avoiding front-heavy scheduling
    - Better work-life balance

    This class inherits common workflow from OptimizationStrategy
    and only implements strategy-specific allocation logic.
    """

    def __init__(self, config: Config):
        """Initialize strategy with balanced allocator.

        Args:
            config: Application configuration
        """
        self.config = config
        self.allocator = BalancedAllocator(config)

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block using balanced allocator.

        Args:
            task: Task to schedule
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        return self.allocator.allocate(
            task, start_date, max_hours_per_day, self.daily_allocations, self.repository
        )
