"""Workload calculation strategies."""

from taskdog_core.application.queries.strategies.workload_calculation_strategy import (
    ActualScheduleStrategy,
    WeekdayOnlyStrategy,
    WorkloadCalculationStrategy,
)

__all__ = [
    "ActualScheduleStrategy",
    "WeekdayOnlyStrategy",
    "WorkloadCalculationStrategy",
]
