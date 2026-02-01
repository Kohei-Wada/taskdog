"""Base workload calculator for calculating daily workload from tasks.

DEPRECATED: This module is kept for backward compatibility only.
For new code, use strategies directly from:
    taskdog_core.application.queries.workload._strategies

Examples:
    # For display (Gantt charts)
    from taskdog_core.application.queries.workload._strategies import ActualScheduleStrategy
    strategy = ActualScheduleStrategy(holiday_checker)
    daily_hours = strategy.compute_from_planned_period(task)

    # For optimization
    from taskdog_core.application.queries.workload._strategies import WeekdayOnlyStrategy
    strategy = WeekdayOnlyStrategy()
    daily_hours = task.daily_allocations or strategy.compute_from_planned_period(task)
"""

from taskdog_core.application.queries.workload._strategies import (
    WeekdayOnlyStrategy,
    WorkloadCalculationStrategy,
)


class BaseWorkloadCalculator:
    """Base class for workload calculators.

    DEPRECATED: This class is kept for backward compatibility only.
    For new code, use strategies directly.

    This base class holds a strategy for computing workload from planned periods.
    OptimizationWorkloadCalculator inherits from this class.
    """

    def __init__(self, strategy: WorkloadCalculationStrategy | None = None):
        """Initialize the workload calculator.

        Args:
            strategy: Strategy for computing workload from planned periods.
                     Defaults to WeekdayOnlyStrategy for backward compatibility.
        """
        self.strategy = strategy or WeekdayOnlyStrategy()
