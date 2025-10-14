"""DTO for removing a task."""

from dataclasses import dataclass


@dataclass
class RemoveTaskInput:
    """Input data for removing a task.

    Attributes:
        task_id: ID of the task to remove
    """

    task_id: int
