"""DTO for simulating task schedules."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SimulateTaskRequest:
    """Request data for task simulation.

    Simulates a virtual task without saving to the database to predict
    completion dates and workload impact.

    Attributes:
        estimated_duration: Required estimated hours for the virtual task
        name: Name of the virtual task (for display purposes)
        priority: Task priority (1-10, default: 5)
        deadline: Optional deadline for the virtual task
        depends_on: List of existing task IDs this virtual task depends on
        algorithm_name: Name of optimization algorithm to use (default: greedy)
        max_hours_per_day: Maximum work hours per day (default: 6.0)
        start_date: Starting date for optimization (defaults to next weekday)
        force_override: Whether to override existing schedules (default: False)
    """

    estimated_duration: float
    name: str = "Simulated Task"
    priority: int = 5
    deadline: datetime | None = None
    depends_on: list[int] = field(default_factory=list)
    algorithm_name: str = "greedy"
    max_hours_per_day: float = 6.0
    start_date: datetime | None = None
    force_override: bool = False
