"""DTO for creating a task."""

from dataclasses import dataclass


@dataclass
class CreateTaskInput:
    """Input data for creating a task.

    Attributes:
        name: Task name
        priority: Task priority (higher value = higher priority)
        planned_start: Planned start datetime string (optional)
        planned_end: Planned end datetime string (optional)
        deadline: Deadline datetime string (optional)
        estimated_duration: Estimated duration in hours (optional)
        is_fixed: Whether task schedule is fixed and shouldn't be changed by optimizer (optional)
    """

    name: str
    priority: int
    planned_start: str | None = None
    planned_end: str | None = None
    deadline: str | None = None
    estimated_duration: float | None = None
    is_fixed: bool = False
