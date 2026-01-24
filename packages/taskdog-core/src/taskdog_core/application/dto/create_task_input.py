"""DTO for creating a task."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateTaskInput:
    """Request data for creating a task.

    Attributes:
        name: Task name
        priority: Task priority (higher value = higher priority), or None if not set
        planned_start: Planned start datetime (optional)
        planned_end: Planned end datetime (optional)
        deadline: Deadline datetime (optional)
        estimated_duration: Estimated duration in hours (optional)
        is_fixed: Whether task schedule is fixed and shouldn't be changed by optimizer (optional)
        tags: List of tags for categorization and filtering (optional)
    """

    name: str
    priority: int | None = None
    planned_start: datetime | None = None
    planned_end: datetime | None = None
    deadline: datetime | None = None
    estimated_duration: float | None = None
    is_fixed: bool = False
    tags: list[str] | None = None
