"""Optimization workload calculator for schedule optimization."""

from typing import TYPE_CHECKING

from taskdog_core.application.queries.workload._strategies import (
    AllDaysStrategy,
    WeekdayOnlyStrategy,
)
from taskdog_core.application.queries.workload.base import BaseWorkloadCalculator

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class OptimizationWorkloadCalculator(BaseWorkloadCalculator):
    """Workload calculator for schedule optimization and auto-scheduling.

    By default, this calculator distributes task hours only across weekdays
    (Monday-Friday), which is the standard assumption for automated task scheduling.

    When include_all_days=True, hours are distributed across all days including
    weekends and holidays.

    ## Purpose

    Use this calculator when:
    - Running schedule optimization algorithms
    - Calculating capacity for work planning
    - Auto-scheduling tasks

    ## Behavior

    Default (include_all_days=False):
    - Distributes hours only across weekdays (Mon-Fri)
    - Weekends are completely excluded
    - Weekend-only tasks return empty allocation (0 hours)

    With include_all_days=True:
    - Distributes hours across all days (including weekends/holidays)
    - All days are included in workload calculation

    ## Usage

    ```python
    # Basic usage (weekdays only)
    calculator = OptimizationWorkloadCalculator()

    # Include weekends and holidays
    calculator = OptimizationWorkloadCalculator(include_all_days=True)

    # With holiday checker
    calculator = OptimizationWorkloadCalculator(holiday_checker=my_checker)

    # Calculate workload
    daily_workload = calculator.calculate_daily_workload(tasks, start, end)

    # Get single task hours
    task_hours = calculator.get_task_daily_hours(task)
    ```
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
