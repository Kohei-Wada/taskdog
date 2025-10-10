"""DTO for creating a task."""

from dataclasses import dataclass


@dataclass
class CreateTaskInput:
    """Input data for creating a task.

    Attributes:
        name: Task name
        priority: Task priority (default: 100, higher value = higher priority)
        planned_start: Planned start datetime string (optional)
        planned_end: Planned end datetime string (optional)
        deadline: Deadline datetime string (optional)
        estimated_duration: Estimated duration in hours (optional)
    """

    name: str
    priority: int = 100
    planned_start: str | None = None
    planned_end: str | None = None
    deadline: str | None = None
    estimated_duration: float | None = None
