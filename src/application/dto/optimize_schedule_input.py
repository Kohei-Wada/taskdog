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
        algorithm_name: Name of optimization algorithm to use
    """

    start_date: datetime
    max_hours_per_day: float
    force_override: bool
    algorithm_name: str
