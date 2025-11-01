"""Task status enum for presentation layer.

This is a presentation-layer enum that mirrors the domain TaskStatus but maintains
clean separation between layers. This allows the presentation layer to have its own
status representation independent of domain changes.
"""

from enum import Enum


class TaskStatus(Enum):
    """Task status values for presentation layer.

    This enum represents task statuses in the presentation layer (UI, ViewModels).
    It is intentionally separate from domain.entities.task.TaskStatus to maintain
    proper layer separation in Clean Architecture.

    Values should be converted from domain entities using TaskMapper.
    """

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"

    @property
    def value(self) -> str:
        """Get the string value of the status.

        Returns:
            The status as a string (e.g., "PENDING", "IN_PROGRESS")
        """
        return self._value_
