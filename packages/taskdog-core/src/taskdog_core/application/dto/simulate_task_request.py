"""DTO for simulating task schedules."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SimulateTaskRequest:
    """Request data for task simulation.

    Simulates a virtual task without saving to the database to predict
    completion dates and workload impact.

    Uses the same interface as CreateTaskRequest for consistency.
    System automatically tries all algorithms and returns the best result.

    Attributes:
        estimated_duration: Required estimated hours for the virtual task
        name: Name of the virtual task (for display purposes)
        priority: Task priority (1-10, default: 5)
        deadline: Optional deadline for the virtual task
        depends_on: List of existing task IDs this virtual task depends on
        tags: List of tags for categorization
        is_fixed: Whether task is fixed (won't be rescheduled)
        max_hours_per_day: Maximum work hours per day (default: 6.0)
    """

    estimated_duration: float
    name: str
    priority: int = 5
    deadline: datetime | None = None
    depends_on: list[int] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    is_fixed: bool = False
    max_hours_per_day: float = 6.0
