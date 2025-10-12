from abc import ABC, abstractmethod

from domain.entities.task import Task


class TaskFormatter(ABC):
    """Abstract interface for task formatting."""

    @abstractmethod
    def format_tasks(self, tasks: list[Task], task_manager) -> str:
        """Format tasks into string representation.

        Args:
            tasks: List of all tasks to format
            task_manager: TaskManager instance for accessing task relationships

        Returns:
            Formatted string representation of tasks
        """
        pass
