"""DTO for optimizing task schedules."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class OptimizeScheduleInput:
    """Request data for schedule optimization.

    Attributes:
        start_date: Starting date for optimization (datetime object)
        max_hours_per_day: Maximum work hours per day
        force_override: Whether to override existing schedules
        algorithm_name: Name of optimization algorithm to use
        current_time: Current time for calculating remaining hours on the start date (defaults to None)
    """

    start_date: datetime
    max_hours_per_day: float
    force_override: bool
    algorithm_name: str
    current_time: datetime | None = None
