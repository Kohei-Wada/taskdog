"""Earliest Deadline First (EDF) optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.workload_allocator import WorkloadAllocator
from domain.entities.task import Task


class EarliestDeadlineOptimizationStrategy(OptimizationStrategy):
    """Earliest Deadline First (EDF) algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on deadline proximity:
    1. Sort tasks by deadline (earliest first)
    2. Tasks without deadlines are scheduled last
    3. Allocate time blocks sequentially in deadline order
    4. Ignore priority field completely

    This class inherits common workflow from OptimizationStrategy
    and only implements strategy-specific sorting and allocation logic.
    """

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
            key=lambda t: t.deadline if t.deadline is not None else datetime.max,
        )

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
