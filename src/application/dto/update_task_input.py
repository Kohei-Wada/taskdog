"""DTO for updating a task."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class UpdateTaskInput:
    """Input data for updating a task.

    Attributes:
        task_id: ID of the task to update
        priority: New priority (optional)
        status: New status (optional)
        planned_start: New planned start (optional)
        planned_end: New planned end (optional)
        deadline: New deadline (optional)
        estimated_duration: New estimated duration (optional)
    """

    task_id: int
    priority: Optional[int] = None
    status: Optional[str] = None
    planned_start: Optional[str] = None
    planned_end: Optional[str] = None
    deadline: Optional[str] = None
    estimated_duration: Optional[float] = None
