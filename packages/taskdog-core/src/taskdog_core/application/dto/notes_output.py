"""Output DTO for notes operations."""

from dataclasses import dataclass


@dataclass
class NotesOutput:
    """Output DTO for notes operations.

    Attributes:
        task_id: Task ID
        task_name: Task name (used for WebSocket broadcast messages)
        content: Notes content (markdown)
        has_notes: Whether the task has non-empty notes
    """

    task_id: int
    task_name: str
    content: str
    has_notes: bool
