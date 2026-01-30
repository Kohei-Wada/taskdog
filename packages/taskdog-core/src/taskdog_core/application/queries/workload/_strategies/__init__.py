"""Internal workload calculation strategies.

This module is internal to the workload package. External code should use
the public calculators (OptimizationWorkloadCalculator, DisplayWorkloadCalculator)
instead of accessing strategies directly.
"""

from taskdog_core.application.queries.workload._strategies.actual_schedule import (
    ActualScheduleStrategy,
)
from taskdog_core.application.queries.workload._strategies.base import (
    WorkloadCalculationStrategy,
)
from taskdog_core.application.queries.workload._strategies.weekday_only import (
    WeekdayOnlyStrategy,
)

__all__ = [
    "ActualScheduleStrategy",
    "WeekdayOnlyStrategy",
    "WorkloadCalculationStrategy",
]
