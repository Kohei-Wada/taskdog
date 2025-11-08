from abc import ABC, abstractmethod
from typing import Any

from taskdog_core.domain.entities.task import Task


class TaskRenderer(ABC):
    """Abstract interface for task rendering."""

    @abstractmethod
    def render(self, tasks: list[Task], task_manager: Any) -> None:
        """Render tasks to output.

        Args:
            tasks: List of all tasks to render
            task_manager: TaskManager instance for accessing task relationships
        """
        pass
