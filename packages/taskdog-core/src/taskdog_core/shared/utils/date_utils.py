"""Date and time utility functions for task scheduling.

This module provides utilities for:
- Parsing datetime strings (parse_date, parse_datetime)
- Weekday/weekend detection (is_weekday, is_weekend)
- Workday calculations (count_weekdays, get_previous_monday, calculate_next_workday, get_next_weekday)
- Date range calculations (get_today_range, get_this_week_range)

Note: Monday=0, Tuesday=1, ..., Friday=4, Saturday=5, Sunday=6
"""

from datetime import date, datetime, timedelta

from taskdog_core.shared.config_manager import ConfigManager
from taskdog_core.shared.constants import WEEKDAY_THRESHOLD
from taskdog_core.shared.constants.formats import DATETIME_FORMAT


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


def is_weekday(dt: datetime | date) -> bool:
    """Check if a date is a weekday (Monday-Friday).

    Args:
        dt: Date or datetime to check

    Returns:
        True if Monday-Friday, False if Saturday-Sunday
    """
    return dt.weekday() < WEEKDAY_THRESHOLD


def is_weekend(dt: datetime | date) -> bool:
    """Check if a date is a weekend (Saturday-Sunday).

    Args:
        dt: Date or datetime to check

    Returns:
        True if Saturday-Sunday, False if Monday-Friday
    """
    return dt.weekday() >= WEEKDAY_THRESHOLD


def count_weekdays(start: datetime | date, end: datetime | date) -> int:
    """Count weekdays (Monday-Friday) in a date range.

    Args:
        start: Start date (inclusive) - can be date or datetime
        end: End date (inclusive) - can be date or datetime

    Returns:
        Number of weekdays in the range
    """
    # Convert datetime to date for comparison
    start_date = start.date() if isinstance(start, datetime) else start
    end_date = end.date() if isinstance(end, datetime) else end

    weekday_count = 0
    current_date = start_date
    while current_date <= end_date:
        if is_weekday(current_date):
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

    # If today is a weekday, use today
    if is_weekday(today):
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

    # Skip weekends - move to next Monday if needed
    while is_weekend(next_day):
        next_day += timedelta(days=1)

    # Set time to default_start_hour from config (default: 9:00) for schedule start times
    return next_day.replace(
        hour=config.time.default_start_hour, minute=0, second=0, microsecond=0
    )


def get_today_range() -> tuple[date, date]:
    """Get the date range for today (start and end are the same date).

    This is useful for filtering tasks that are relevant for today.

    Returns:
        Tuple of (start_date, end_date) where both are today's date
    """
    today = date.today()
    return today, today


def get_this_week_range() -> tuple[date, date]:
    """Get the date range for this week (Monday through Sunday).

    Returns:
        Tuple of (start_date, end_date) where start is Monday and end is Sunday
    """
    today = date.today()
    # Get the Monday of this week (weekday() returns 0 for Monday)
    week_start = today - timedelta(days=today.weekday())
    # Get the Sunday of this week
    week_end = week_start + timedelta(days=6)
    return week_start, week_end
