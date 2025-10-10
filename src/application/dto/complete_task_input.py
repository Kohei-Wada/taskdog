"""DTO for completing a task."""

from dataclasses import dataclass


@dataclass
class CompleteTaskInput:
    """Input data for completing a task.

    Attributes:
        task_id: ID of the task to complete
    """

    task_id: int
