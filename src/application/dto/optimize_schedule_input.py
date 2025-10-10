"""DTO for optimizing task schedules."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class OptimizeScheduleInput:
    """Input data for schedule optimization.

    Attributes:
        start_date: Starting date for optimization (datetime object)
        max_hours_per_day: Maximum work hours per day
        force_override: Whether to override existing schedules
        dry_run: If True, only return preview without saving
        algorithm_name: Name of optimization algorithm to use (default: "greedy")
    """

    start_date: datetime
    max_hours_per_day: float = 6.0
    force_override: bool = False
    dry_run: bool = False
    algorithm_name: str = "greedy"
