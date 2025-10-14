"""DTO for archiving a task."""

from dataclasses import dataclass


@dataclass
class ArchiveTaskInput:
    """Input data for archiving a task.

    Attributes:
        task_id: ID of the task to archive
    """

    task_id: int
