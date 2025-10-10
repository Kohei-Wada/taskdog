"""DTO for removing a task."""

from dataclasses import dataclass


@dataclass
class RemoveTaskInput:
    """Input data for removing a task.

    Attributes:
        task_id: ID of the task to remove
        cascade: If True, delete all children recursively; if False, orphan children
    """

    task_id: int
    cascade: bool = False
