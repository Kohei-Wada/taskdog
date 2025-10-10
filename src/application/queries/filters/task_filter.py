"""Base class for task filters."""

from abc import ABC, abstractmethod

from domain.entities.task import Task


class TaskFilter(ABC):
    """Abstract base class for task filters.

    Filters apply criteria to select a subset of tasks from a collection.
    Concrete filters implement specific filtering logic (e.g., today's tasks,
    incomplete tasks, tasks within a date range).
    """

    @abstractmethod
    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks based on specific criteria.

        Args:
            tasks: List of all tasks to filter

        Returns:
            Filtered list of tasks matching the criteria
        """
        pass
