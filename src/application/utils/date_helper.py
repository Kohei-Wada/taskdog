"""Date utility functions for application layer (business logic).

This module provides business-logic-aware date utilities that depend on
domain services like HolidayChecker.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING

from shared.utils.date_utils import is_weekday

if TYPE_CHECKING:
    from domain.services.holiday_checker import IHolidayChecker


def is_workday(dt: datetime | date, holiday_checker: "IHolidayChecker | None" = None) -> bool:
    """Check if a date is a workday (weekday and not a holiday).

    Args:
        dt: Date or datetime to check
        holiday_checker: Optional IHolidayChecker instance for holiday detection.
                         If None, only weekday/weekend is checked.

    Returns:
        True if the date is a weekday AND not a holiday,
        False if weekend or holiday

    Examples:
        >>> is_workday(date(2025, 1, 6))  # Monday
        True
        >>> is_workday(date(2025, 1, 4))  # Saturday
        False

        >>> from infrastructure.holiday_checker import HolidayChecker
        >>> checker = HolidayChecker("JP")
        >>> is_workday(date(2025, 1, 1), checker)  # New Year's Day
        False
    """
    if not is_weekday(dt):
        return False

    if holiday_checker is None:
        return True

    # Convert datetime to date for holiday checking
    check_date = dt.date() if isinstance(dt, datetime) else dt
    return not holiday_checker.is_holiday(check_date)
