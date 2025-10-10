"""DTO for optimization summary data."""

from dataclasses import dataclass

from domain.entities.task import Task


@dataclass
class OptimizationSummary:
    """Summary data from schedule optimization.

    Attributes:
        new_count: Number of newly scheduled tasks
        rescheduled_count: Number of rescheduled tasks (force mode)
        total_hours: Total estimated hours of optimized tasks
        deadline_conflicts: Number of tasks where planned_end > deadline
        days_span: Number of days covered by schedule
        unscheduled_tasks: Tasks that could not be scheduled
        overloaded_days: List of (date_str, hours) tuples exceeding max hours
    """

    new_count: int
    rescheduled_count: int
    total_hours: float
    deadline_conflicts: int
    days_span: int
    unscheduled_tasks: list[Task]
    overloaded_days: list[tuple[str, float]]
