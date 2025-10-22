"""Utilities for parsing datetime strings."""

from datetime import date, datetime, timedelta

from domain.constants import DATETIME_FORMAT
from shared.config_manager import ConfigManager
from shared.constants import WEEKDAY_THRESHOLD


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
        # Skip weekends (Saturday and Sunday)
        if current_date.weekday() < WEEKDAY_THRESHOLD:
            weekday_count += 1
        current_date += timedelta(days=1)
    return weekday_count


def get_previous_monday(from_date: date | None = None) -> date:
    """Get the previous Monday (or today if today is Monday).

    Args:
        from_date: Optional date to calculate from (defaults to today)

    Returns:
        date object representing the previous Monday
    """
    target_date = from_date or date.today()
    # weekday(): Monday=0, Sunday=6
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)


def calculate_next_workday(start_date: datetime | None = None) -> datetime:
    """Calculate the next available workday.

    If the given date (or today if None) is a weekday, returns that date.
    Otherwise, returns the next Monday.

    Args:
        start_date: Starting date (default: today)

    Returns:
        The next workday (Monday-Friday)
    """
    today = start_date if start_date else datetime.now()

    # If today is a weekday (Monday=0, Friday=4), use today
    if today.weekday() < 5:
        return today

    # Otherwise, move to next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:  # If today is Sunday
        days_until_monday = 1
    return today + timedelta(days=days_until_monday)


def get_next_weekday() -> datetime:
    """Get the next weekday (skip weekends).

    Returns:
        datetime object representing the next weekday at default_start_hour from config
    """
    config = ConfigManager.load()
    today = datetime.now()
    next_day = today + timedelta(days=1)

    # If next day is Saturday or Sunday, move to Monday
    while next_day.weekday() >= WEEKDAY_THRESHOLD:
        next_day += timedelta(days=1)

    # Set time to default_start_hour from config (default: 9:00) for schedule start times
    return next_day.replace(hour=config.time.default_start_hour, minute=0, second=0, microsecond=0)
