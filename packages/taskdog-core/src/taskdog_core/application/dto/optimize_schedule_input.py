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
        task_ids: Specific task IDs to optimize (None means all schedulable tasks)
        include_all_days: If True, schedule tasks on weekends and holidays too (default: False)
    """

    start_date: datetime
    max_hours_per_day: float
    force_override: bool
    algorithm_name: str
    task_ids: list[int] | None = None
    include_all_days: bool = False
