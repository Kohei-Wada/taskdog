"""Greedy optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.allocators.greedy_forward_allocator import (
    GreedyForwardAllocator,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.sorters.optimization_task_sorter import OptimizationTaskSorter
from domain.entities.task import Task
from shared.config_manager import Config


class GreedyOptimizationStrategy(OptimizationStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Sort tasks by priority (deadline urgency, priority field, task ID)
    2. Allocate time blocks sequentially in priority order
    3. Fill available time slots from start_date onwards (greedy forward allocation)

    The greedy allocation fills each day to its maximum capacity before
    moving to the next day, prioritizing early completion.
    """

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
        """Sort tasks by priority (greedy approach).

        Uses OptimizationTaskSorter which considers:
        - Deadline urgency (closer deadline = higher priority)
        - Priority field value
        - Task ID (for stable sorting)

        Args:
            tasks: Filtered schedulable tasks
            start_date: Starting date for schedule optimization
            repository: Task repository for hierarchy queries

        Returns:
            Tasks sorted by priority (highest priority first)
        """
        sorter = OptimizationTaskSorter(start_date, repository)
        return sorter.sort_by_priority(tasks)

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
