"""Greedy optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.workload_allocator import WorkloadAllocator
from application.sorters.optimization_task_sorter import OptimizationTaskSorter
from domain.entities.task import Task


class GreedyOptimizationStrategy(OptimizationStrategy):
    """Greedy algorithm for task scheduling optimization.

    This strategy uses a greedy approach to schedule tasks:
    1. Sort tasks by priority (deadline urgency, priority field, task ID)
    2. Allocate time blocks sequentially in priority order
    3. Fill available time slots from start_date onwards

    This class inherits common workflow from OptimizationStrategy
    and only implements strategy-specific sorting and allocation logic.
    """

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
        allocator: WorkloadAllocator,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block using greedy forward allocation.

        Uses WorkloadAllocator's standard greedy allocation which
        fills time slots from start_date onwards.

        Args:
            task: Task to schedule
            allocator: Workload allocator (for tracking daily_allocations)
            start_date: Starting date for allocation
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        return allocator.allocate_timeblock(task)
