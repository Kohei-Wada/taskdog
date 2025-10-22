"""Greedy optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task
from shared.config_manager import Config


class GreedyOptimizationStrategy(OptimizationStrategy):
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

    def __init__(self, config: Config):
        """Initialize strategy with greedy forward allocator.

        Args:
            config: Application configuration
        """
        self.config = config

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block using greedy forward allocator.

        Args:
            task: Task to schedule
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        # Create allocator with holiday_checker (available after optimize_tasks sets it)
        allocator = GreedyForwardAllocator(self.config, self.holiday_checker)
        return allocator.allocate(
            task, start_date, max_hours_per_day, self.daily_allocations, self.repository
        )
