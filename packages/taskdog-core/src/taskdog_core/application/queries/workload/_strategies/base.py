"""Base class for workload calculation strategies."""

from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import TYPE_CHECKING

from taskdog_core.domain.entities.task import Task
from taskdog_core.shared.utils.date_utils import is_weekday

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class WorkloadCalculationStrategy(ABC):
    """Abstract base class for workload calculation strategies.

    Different strategies implement different business rules for how to
    distribute task hours when daily_allocations is not explicitly set.

    ## Responsibility

    This abstract class defines the contract for workload calculation strategies
    and provides common utility methods for determining working days.

    ## Strategy Pattern

    Subclasses implement `compute_from_planned_period()` to define how task hours
    should be distributed across the scheduled period. This allows different
    business rules for different contexts (optimization vs. display).

    ## Holiday Support

    The strategy can optionally accept a `HolidayChecker` to exclude holidays
    when calculating working days. This is particularly useful for display/reporting
    to match real-world work patterns.

    ## Common Utilities

    - `is_working_day(date)`: Check if a date is a working day (weekday AND non-holiday)
    - `count_working_days(start, end)`: Count working days in a date range

    These utilities ensure consistent working day logic across all strategies.
    """

    def __init__(self, holiday_checker: "IHolidayChecker | None" = None):
        """Initialize the strategy with an optional holiday checker.

        Args:
            holiday_checker: Optional holiday checker for excluding holidays.
                           If None, only weekends are excluded (weekday check only).
        """
        self.holiday_checker = holiday_checker

    @abstractmethod
    def compute_from_planned_period(self, task: Task) -> dict[date, float]:
        """Compute daily hours by distributing across the planned period.

        This method is called when a task has no explicit daily_allocations
        (i.e., not scheduled by optimizer). The strategy determines how to
        distribute the estimated_duration across the planned period.

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping date to hours {date: hours}.
            Empty dict if task is missing required fields.
        """
        pass

    def is_working_day(self, check_date: date) -> bool:
        """Check if a date is a working day (weekday and not a holiday).

        Args:
            check_date: Date to check

        Returns:
            True if the date is a working day, False otherwise
        """
        if not is_weekday(check_date):
            return False
        return not (
            self.holiday_checker and self.holiday_checker.is_holiday(check_date)
        )

    def count_working_days(self, start_date: date, end_date: date) -> int:
        """Count working days (weekdays excluding holidays) in a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Number of working days
        """
        count = 0
        current_date = start_date
        while current_date <= end_date:
            if self.is_working_day(current_date):
                count += 1
            current_date += timedelta(days=1)
        return count
