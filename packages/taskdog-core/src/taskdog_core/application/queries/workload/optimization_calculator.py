"""Optimization workload calculator for schedule optimization."""

from typing import TYPE_CHECKING

from taskdog_core.application.queries.workload._strategies import WeekdayOnlyStrategy
from taskdog_core.application.queries.workload.base import BaseWorkloadCalculator

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class OptimizationWorkloadCalculator(BaseWorkloadCalculator):
    """Workload calculator for schedule optimization and auto-scheduling.

    This calculator distributes task hours only across weekdays (Monday-Friday),
    which is the standard assumption for automated task scheduling.

    ## Purpose

    Use this calculator when:
    - Running schedule optimization algorithms
    - Calculating capacity for work planning
    - Auto-scheduling tasks

    ## Behavior

    - Distributes hours only across weekdays (Mon-Fri)
    - Weekends are completely excluded
    - Weekend-only tasks return empty allocation (0 hours)

    ## Usage

    ```python
    # Basic usage
    calculator = OptimizationWorkloadCalculator()

    # With holiday checker (for future holiday-aware optimization)
    calculator = OptimizationWorkloadCalculator(holiday_checker=my_checker)

    # Calculate workload
    daily_workload = calculator.calculate_daily_workload(tasks, start, end)

    # Get single task hours
    task_hours = calculator.get_task_daily_hours(task)
    ```

    ## Future Extensions

    The holiday_checker parameter is reserved for future features:
    - Holiday-aware scheduling
    - Weekend work configuration (include_weekends parameter)
    """

    def __init__(self, holiday_checker: "IHolidayChecker | None" = None):
        """Initialize the optimization workload calculator.

        Args:
            holiday_checker: Optional holiday checker for future holiday-aware
                           scheduling. Currently reserved for future use.
        """
        # WeekdayOnlyStrategy ignores holidays by design for optimization
        # (optimizer handles holidays separately)
        super().__init__(WeekdayOnlyStrategy(holiday_checker))
