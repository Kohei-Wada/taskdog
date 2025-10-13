"""Abstract base class for optimization strategies."""

from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.task import Task


class OptimizationStrategy(ABC):
    """Abstract base class for task scheduling optimization strategies.

    Different algorithms can implement this interface to provide
    alternative scheduling approaches (greedy, genetic, dynamic programming, etc.).
    """

    @abstractmethod
    def optimize_tasks(
        self,
        tasks: list[Task],
        repository,
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
    ) -> tuple[list[Task], dict[str, float]]:
        """Optimize task schedules using a specific algorithm.

        Args:
            tasks: List of all tasks to consider for optimization
            repository: Task repository for hierarchy queries
            start_date: Starting date for schedule optimization
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules

        Returns:
            Tuple of (modified_tasks, daily_allocations)
            - modified_tasks: List of tasks with updated schedules
            - daily_allocations: Dict mapping date strings to allocated hours
        """
        pass
