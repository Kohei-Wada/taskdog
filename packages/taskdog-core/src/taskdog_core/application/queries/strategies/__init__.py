"""Workload calculation strategies.

This module is deprecated. Please use the workload subpackage instead:

    from taskdog_core.application.queries.workload import (
        OptimizationWorkloadCalculator,
        DisplayWorkloadCalculator,
    )
"""

# Re-export from new location for backward compatibility
from taskdog_core.application.queries.workload._strategies import (
    ActualScheduleStrategy,
    WeekdayOnlyStrategy,
    WorkloadCalculationStrategy,
)

__all__ = [
    "ActualScheduleStrategy",
    "WeekdayOnlyStrategy",
    "WorkloadCalculationStrategy",
]
