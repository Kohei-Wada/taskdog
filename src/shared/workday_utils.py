"""Workday calculation utilities."""

from datetime import datetime, timedelta

from shared.constants import WEEKDAY_THRESHOLD


class WorkdayUtils:
    """Utility class for workday-related calculations.

    This class provides common date/time utilities used by scheduling algorithms
    to distinguish between weekdays and weekends.
    """

    @staticmethod
    def is_weekend(date: datetime) -> bool:
        """Check if a date is a weekend.

        Args:
            date: Date to check

        Returns:
            True if Saturday or Sunday, False otherwise
        """
        return date.weekday() >= WEEKDAY_THRESHOLD  # Friday is last weekday (Mon=0, Fri=4)

    @staticmethod
    def count_weekdays(start_date: datetime, end_date: datetime) -> int:
        """Count weekdays between start and end date (inclusive).

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Number of weekdays (Monday-Friday)
        """
        count = 0
        current = start_date
        while current <= end_date:
            if current.weekday() < WEEKDAY_THRESHOLD:  # Monday=0 to Friday=4
                count += 1
            current += timedelta(days=1)
        return count
