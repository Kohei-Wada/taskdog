"""DTO for simulation results."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class SimulationResult:
    """Result of task simulation.

    Contains information about whether the virtual task can be scheduled,
    when it would be completed, and workload analysis.

    Attributes:
        is_schedulable: Whether the virtual task can be scheduled
        planned_start: Planned start datetime (None if not schedulable)
        planned_end: Planned end datetime (None if not schedulable)
        failure_reason: Human-readable reason if scheduling failed (None if schedulable)
        daily_allocations: Daily hour allocations for the virtual task {date: hours}
        peak_workload: Maximum workload hours on any single day
        peak_date: Date of peak workload (None if no workload)
        average_workload: Average workload hours per day
        total_workload_days: Number of days with allocated work
        virtual_task_name: Name of the simulated task
        estimated_duration: Estimated duration in hours
        priority: Priority of the simulated task
        deadline: Deadline of the simulated task (None if not set)
    """

    is_schedulable: bool
    planned_start: datetime | None
    planned_end: datetime | None
    failure_reason: str | None
    daily_allocations: dict[date, float]
    peak_workload: float
    peak_date: date | None
    average_workload: float
    total_workload_days: int
    virtual_task_name: str
    estimated_duration: float
    priority: int
    deadline: datetime | None
