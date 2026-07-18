"""Output DTO for the executable-task ranking query."""

from __future__ import annotations

from pydantic import BaseModel, Field

from taskdog_core.application.dto.task_dto import TaskRowDto

RANKING_BASIS: list[str] = [
    "in_progress_first",
    "deadline_asc",
    "priority_desc",
    "estimate_asc",
    "id_asc",
]


class NextTasksOutput(BaseModel):
    """Ranked executable tasks. Index 0 is the next task to work on."""

    tasks: list[TaskRowDto]
    ranking_basis: list[str] = Field(default_factory=lambda: list(RANKING_BASIS))
