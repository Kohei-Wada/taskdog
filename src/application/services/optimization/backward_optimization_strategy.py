"""Backward optimization strategy implementation."""

from datetime import datetime
from typing import TYPE_CHECKING

from application.services.optimization.allocators.backward_allocator import (
    BackwardAllocator,
)
from application.services.optimization.optimization_strategy import OptimizationStrategy
from domain.entities.task import Task
from shared.config_manager import Config

if TYPE_CHECKING:
    from domain.repositories.task_repository import TaskRepository


class BackwardOptimizationStrategy(OptimizationStrategy):
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

    This class inherits common workflow from OptimizationStrategy
    and only implements strategy-specific sorting and allocation logic.
    """

    DISPLAY_NAME = "Backward"
    DESCRIPTION = "Just-in-time from deadlines"

    def __init__(self, config: Config):
        """Initialize strategy with configuration.

        Args:
            config: Application configuration
        """
        self.config = config

    def _sort_schedulable_tasks(
        self, tasks: list[Task], start_date: datetime, repository: "TaskRepository"
    ) -> list[Task]:
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

    def _allocate_task(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
    ) -> Task | None:
        """Allocate time block using backward allocator.

        Args:
            task: Task to schedule
            start_date: Earliest allowed start date
            max_hours_per_day: Maximum hours per day

        Returns:
            Copy of task with updated schedule, or None if allocation fails
        """
        # Create allocator with holiday_checker and current_time (available after optimize_tasks sets it)
        allocator = BackwardAllocator(self.config, self.holiday_checker, self.current_time)
        return allocator.allocate(
            task, start_date, max_hours_per_day, self.daily_allocations, self.repository
        )
