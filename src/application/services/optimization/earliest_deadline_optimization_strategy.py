"""Earliest Deadline First (EDF) optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task
from shared.config_manager import Config


class EarliestDeadlineOptimizationStrategy(OptimizationStrategy):
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

    def __init__(self, config: Config):
        """Initialize strategy with configuration.

        Args:
            config: Application configuration
        """
        self.config = config

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository
    ) -> list[Task]:
        """Sort tasks by deadline (earliest first).

        Tasks are sorted by deadline in ascending order
        (earliest deadline = scheduled first). Tasks without deadlines
        are scheduled last (treated as infinite deadline).

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Tasks sorted by deadline (earliest deadline first)
        """
        return sorted(
            tasks,
            key=lambda t: t.deadline
            if t.deadline is not None
            else datetime(9999, 12, 31, 23, 59, 59),
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
        # Create allocator with holiday_checker (available after optimize_tasks sets it)
        allocator = GreedyForwardAllocator(self.config, self.holiday_checker)
        return allocator.allocate(
            task, start_date, max_hours_per_day, self.daily_allocations, self.repository
        )
