"""DTO for task detail information."""

from pydantic import BaseModel

from taskdog_core.application.dto.task_dto import TaskDetailDto


class TaskDetailOutput(BaseModel):
    """Result DTO for task detail with notes.

    Attributes:
        task: Task data transfer object
        notes_content: Content of the notes file (optional)
        has_notes: Whether notes file exists
    """

    task: TaskDetailDto
    notes_content: str | None
    has_notes: bool
