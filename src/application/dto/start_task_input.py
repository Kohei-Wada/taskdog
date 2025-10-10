"""DTO for starting a task."""

from dataclasses import dataclass


@dataclass
class StartTaskInput:
    """Input data for starting a task.

    Attributes:
        task_id: ID of the task to start
    """

    task_id: int
