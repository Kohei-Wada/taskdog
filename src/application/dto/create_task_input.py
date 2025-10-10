"""DTO for creating a task."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class CreateTaskInput:
    """Input data for creating a task.

    Attributes:
        name: Task name
        priority: Task priority (default: 100, higher value = higher priority)
        parent_id: ID of parent task (optional)
        planned_start: Planned start datetime string (optional)
        planned_end: Planned end datetime string (optional)
        deadline: Deadline datetime string (optional)
        estimated_duration: Estimated duration in hours (optional)
    """

    name: str
    priority: int = 100
    parent_id: Optional[int] = None
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    deadline: Optional[str] = None
    estimated_duration: Optional[float] = None
