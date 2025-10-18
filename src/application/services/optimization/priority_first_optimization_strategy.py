"""Priority-first optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task
from shared.config_manager import Config


class PriorityFirstOptimizationStrategy(OptimizationStrategy):
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

    def __init__(self, config: Config):
        """Initialize strategy with greedy forward allocator.

        Args:
            config: Application configuration
        """
        self.config = config
        self.allocator = GreedyForwardAllocator(config)

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by priority field only (priority-first approach).

        Tasks are sorted by priority value in descending order
        (higher priority = scheduled first). Tasks without priority go last.

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Tasks sorted by priority (highest priority first)
        """
        return sorted(
            tasks,
            key=lambda t: t.priority if t.priority is not None else -1,
            reverse=True,
        )

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
        return self.allocator.allocate(
            task, start_date, max_hours_per_day, self.daily_allocations, self.repository
        )
