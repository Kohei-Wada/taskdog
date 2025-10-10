"""Utilities for parsing datetime strings."""

from datetime import date, datetime, timedelta

from domain.constants import DATETIME_FORMAT, DEFAULT_START_HOUR


class DateTimeParser:
    """Utilities for parsing datetime strings."""

    @staticmethod
    def parse_date(date_str: str | None) -> date | None:
        """Parse date string to date object.

        Args:
            date_str: Date string in format YYYY-MM-DD HH:MM:SS

        Returns:
            date object or None if parsing fails or input is None
        """
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str, DATETIME_FORMAT)
            return dt.date()
        except ValueError:
            return None

    @staticmethod
    def parse_datetime(date_str: str | None) -> datetime | None:
        """Parse date string to datetime object.

        Args:
            date_str: Date string in format YYYY-MM-DD HH:MM:SS

        Returns:
            datetime object or None if parsing fails or input is None
        """
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, DATETIME_FORMAT)
        except ValueError:
            return None


def count_weekdays(start: date, end: date) -> int:
    """Count weekdays (Monday-Friday) in a date range.

    Args:
        start: Start date (inclusive)
        end: End date (inclusive)

    Returns:
        Number of weekdays in the range
    """
    weekday_count = 0
    current_date = start
    while current_date <= end:
        # Skip weekends (Saturday=5, Sunday=6)
        if current_date.weekday() < 5:
            weekday_count += 1
        current_date += timedelta(days=1)
    return weekday_count


def get_next_weekday() -> datetime:
    """Get the next weekday (skip weekends).

    Returns:
        datetime object representing the next weekday at DEFAULT_START_HOUR
    """
    today = datetime.now()
    next_day = today + timedelta(days=1)

    # If next day is Saturday (5) or Sunday (6), move to Monday
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)

    # Set time to DEFAULT_START_HOUR (9:00) for schedule start times
    return next_day.replace(hour=DEFAULT_START_HOUR, minute=0, second=0, microsecond=0)
