"""DTO for logging actual hours worked on a task."""

from dataclasses import dataclass


@dataclass
class LogHoursInput:
    """Request data for logging actual hours worked.

    Attributes:
        task_id: ID of the task
        date: Date in YYYY-MM-DD format
        hours: Number of hours worked on this date
    """

    task_id: int
    date: str
    hours: float
