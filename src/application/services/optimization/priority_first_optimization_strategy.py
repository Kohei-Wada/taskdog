"""Priority-first optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.optimization_strategy import OptimizationStrategy
from application.services.workload_allocator import WorkloadAllocator
from domain.entities.task import Task


class PriorityFirstOptimizationStrategy(OptimizationStrategy):
    """Priority-first algorithm for task scheduling optimization.

    This strategy schedules tasks purely based on priority field value:
    1. Sort tasks by priority field only (descending: higher priority first)
    2. Allocate time blocks sequentially in priority order
    3. Ignore deadlines completely

    This class inherits common workflow from OptimizationStrategy
    and only implements strategy-specific sorting and allocation logic.
    """

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
