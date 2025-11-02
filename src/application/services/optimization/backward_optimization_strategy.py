"""Backward optimization strategy implementation."""

from datetime import datetime

from application.services.optimization.allocator_based_strategy import AllocatorBasedStrategy
from application.services.optimization.allocators.backward_allocator import (
    BackwardAllocator,
)
from application.services.optimization.allocators.task_allocator_base import TaskAllocatorBase
from domain.entities.task import Task


class BackwardOptimizationStrategy(AllocatorBasedStrategy):
    """Backward (Just-In-Time) algorithm for task scheduling optimization.

    This strategy schedules tasks as late as possible while meeting deadlines:
    1. Sort tasks by deadline (furthest deadline first)
    2. For each task, allocate time blocks backward from deadline
    3. Fill time slots from deadline backwards

    Benefits:
    - Maximum flexibility for requirement changes
    - Prevents early resource commitment
    - Just-In-Time delivery approach
    - Keeps options open longer

    This class inherits common workflow from AllocatorBasedStrategy
    and implements custom sorting logic for backward scheduling.
    """

    DISPLAY_NAME = "Backward"
    DESCRIPTION = "Just-in-time from deadlines"

    def _get_allocator_class(self) -> type[TaskAllocatorBase]:
        """Return BackwardAllocator for this strategy.

        Returns:
            BackwardAllocator class for just-in-time scheduling
        """
        return BackwardAllocator

    def _sort_schedulable_tasks(self, tasks: list[Task], start_date: datetime) -> list[Task]:
        """Sort tasks by deadline (furthest first).

        Tasks without deadlines are placed at the beginning
        (they will be scheduled first = furthest from now).

        Args:
            tasks: Tasks to sort
            start_date: Reference date for deadline calculation

        Returns:
            Sorted task list (furthest deadline first)
        """

        def deadline_key(task: Task) -> tuple[int, int, int | None]:
            if task.deadline:
                deadline_dt = task.deadline
                days_until = (deadline_dt - start_date).days
                # Negative to get furthest first
                return (0, -days_until, task.id)
            else:
                # Tasks without deadline: schedule first (no deadline pressure)
                return (1, 0, task.id)

        return sorted(tasks, key=deadline_key)
