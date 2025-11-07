"""Abstract interface for Task entity mappers.

This interface defines the contract for converting between Task entities
and their persistence representations (JSON, database rows, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any

from taskdog_core.domain.entities.task import Task


class TaskMapperInterface(ABC):
    """Abstract base class for Task entity mappers.

    Mappers are responsible for converting Task entities to and from
    their persistence format. This abstraction allows the domain layer
    to remain independent of the storage mechanism.
    """

    @abstractmethod
    def to_dict(self, task: Task) -> dict[str, Any]:
        """Convert a Task entity to a dictionary representation.

        Args:
            task: The Task entity to serialize

        Returns:
            Dictionary representation suitable for the storage format
        """
        pass

    @abstractmethod
    def from_dict(self, data: dict[str, Any]) -> Task:
        """Convert a dictionary representation to a Task entity.

        Args:
            data: Dictionary containing task data from storage

        Returns:
            Task entity reconstructed from the data

        Raises:
            TaskValidationError: If the data is invalid or incomplete
        """
        pass
