"""DTO for pausing a task."""

from dataclasses import dataclass


@dataclass
class PauseTaskInput:
    """Input data for pausing a task.

    Attributes:
        task_id: ID of the task to pause
    """

    task_id: int
