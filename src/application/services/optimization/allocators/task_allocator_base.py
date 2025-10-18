"""Abstract base class for task allocation strategies."""

from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.task import Task
from shared.config_manager import Config


class TaskAllocatorBase(ABC):
    """Abstract base class for task allocation strategies.

    Allocators are responsible for determining when and how to schedule
    a single task given current resource constraints.

    Each allocator implements a specific scheduling algorithm (greedy,
    balanced, backward, etc.) while the sorting of tasks is handled
    separately by the optimization strategy.
    """

    def __init__(self, config: Config):
        """Initialize allocator with configuration.

        Args:
            config: Application configuration
        """
        self.config = config

    @abstractmethod
    def allocate(
        self,
        task: Task,
        start_date: datetime,
        max_hours_per_day: float,
        daily_allocations: dict[str, float],
        repository,
    ) -> Task | None:
        """Allocate time blocks for a single task.

        Args:
            task: Task to schedule
            start_date: Earliest allowed start date
            max_hours_per_day: Maximum work hours per day
            daily_allocations: Current daily allocations (will be modified)
            repository: Task repository for deadline calculations

        Returns:
            Copy of task with updated schedule (planned_start, planned_end,
            daily_allocations), or None if allocation fails
        """
        pass
