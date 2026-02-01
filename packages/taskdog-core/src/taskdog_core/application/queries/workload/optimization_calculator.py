"""Optimization workload calculator for schedule optimization.

DEPRECATED: This module is kept for backward compatibility only.
For new code, use WeekdayOnlyStrategy directly:

    from taskdog_core.application.queries.workload._strategies import WeekdayOnlyStrategy
    strategy = WeekdayOnlyStrategy()
    daily_hours = task.daily_allocations or strategy.compute_from_planned_period(task)
"""

from typing import TYPE_CHECKING

from taskdog_core.application.queries.workload._strategies import (
    AllDaysStrategy,
    WeekdayOnlyStrategy,
)
from taskdog_core.application.queries.workload.base import BaseWorkloadCalculator

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class OptimizationWorkloadCalculator(BaseWorkloadCalculator):
    """Workload calculator for schedule optimization.

    DEPRECATED: This class is kept for backward compatibility only.
    For new code, use WeekdayOnlyStrategy directly.

    This calculator wraps WeekdayOnlyStrategy (or AllDaysStrategy if include_all_days=True).
    """

    def __init__(
        self,
        holiday_checker: "IHolidayChecker | None" = None,
        include_all_days: bool = False,
    ):
        """Initialize the optimization workload calculator.

        Args:
            holiday_checker: Optional holiday checker for holiday-aware
                           scheduling.
            include_all_days: If True, include weekends and holidays in
                            workload calculation. Default is False.
        """
        if include_all_days:
            # AllDaysStrategy includes all days (weekends, holidays)
            super().__init__(AllDaysStrategy(holiday_checker))
        else:
            # WeekdayOnlyStrategy ignores holidays by design for optimization
            # (optimizer handles holidays separately)
            super().__init__(WeekdayOnlyStrategy(holiday_checker))
