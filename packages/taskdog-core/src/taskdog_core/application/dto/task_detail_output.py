"""DTO for task detail information."""

from dataclasses import dataclass

from taskdog_core.application.dto.task_dto import TaskDetailDto


@dataclass
class TaskDetailOutput:
    """Result DTO for task detail with notes.

    Attributes:
        task: Task data transfer object
        notes_content: Content of the notes file (optional)
        has_notes: Whether notes file exists
    """

    task: TaskDetailDto
    notes_content: str | None
    has_notes: bool
