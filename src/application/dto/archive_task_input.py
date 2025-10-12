"""DTO for archiving a task."""

from dataclasses import dataclass


@dataclass
class ArchiveTaskInput:
    """Input data for archiving a task.

    Attributes:
        task_id: ID of the task to archive
        cascade: If True, archive all children recursively; if False, orphan children
    """

    task_id: int
    cascade: bool = False
