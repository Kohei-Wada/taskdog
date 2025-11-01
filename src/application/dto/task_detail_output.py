"""DTO for task detail information."""

from dataclasses import dataclass

from domain.entities.task import Task


@dataclass
class GetTaskDetailOutput:
    """Result DTO for task detail with notes.

    Attributes:
        task: Task entity
        notes_content: Content of the notes file (optional)
        has_notes: Whether notes file exists
    """

    task: Task
    notes_content: str | None
    has_notes: bool
