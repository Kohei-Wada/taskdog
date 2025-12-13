"""Date and time utility functions for task scheduling.

This module provides utilities for:
- Parsing datetime strings (parse_date, parse_datetime)
- Weekday/weekend detection (is_weekday, is_weekend)
- Workday calculations (count_weekdays, get_previous_monday, calculate_next_workday, get_next_weekday)

Note: Monday=0, Tuesday=1, ..., Friday=4, Saturday=5, Sunday=6
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from taskdog_core.shared.constants import WEEKDAY_THRESHOLD
from taskdog_core.shared.constants.formats import DATETIME_FORMAT

if TYPE_CHECKING:
    from taskdog_core.domain.services.time_provider import ITimeProvider

# Module-level singleton for default time provider (lazy initialization)
_default_time_provider: ITimeProvider | None = None


def _get_time_provider(time_provider: ITimeProvider | None) -> ITimeProvider:
    """Get time provider, defaulting to a cached SystemTimeProvider singleton.

    Uses a module-level singleton to avoid creating multiple instances
    and ensure consistent behavior across calls.

    Args:
        time_provider: Optional time provider

    Returns:
        The provided time_provider or the cached SystemTimeProvider singleton
    """
    if time_provider is not None:
        return time_provider

    global _default_time_provider
    if _default_time_provider is None:
        from taskdog_core.infrastructure.time_provider import SystemTimeProvider

        _default_time_provider = SystemTimeProvider()
    return _default_time_provider


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


def get_previous_monday(
    from_date: date | None = None,
    time_provider: ITimeProvider | None = None,
) -> date:
    """Get the previous Monday (or today if today is Monday).

    Args:
        from_date: Optional date to calculate from (defaults to today)
        time_provider: Provider for current time. Defaults to SystemTimeProvider.

    Returns:
        date object representing the previous Monday
    """
    if from_date is None:
        provider = _get_time_provider(time_provider)
        from_date = provider.today()
    # weekday(): Monday=0, Sunday=6
    days_since_monday = from_date.weekday()
    return from_date - timedelta(days=days_since_monday)


def calculate_next_workday(
    start_date: datetime | None = None,
    time_provider: ITimeProvider | None = None,
) -> datetime:
    """Calculate the next available workday.

    If the given date (or today if None) is a weekday, returns that date.
    Otherwise, returns the next Monday.

    Args:
        start_date: Starting date (default: today)
        time_provider: Provider for current time. Defaults to SystemTimeProvider.

    Returns:
        The next workday (Monday-Friday)
    """
    if start_date is None:
        provider = _get_time_provider(time_provider)
        start_date = provider.now()

    # If today is a weekday, use today
    if is_weekday(start_date):
        return start_date

    # Otherwise, move to next Monday
    days_until_monday = (7 - start_date.weekday()) % 7
    if days_until_monday == 0:  # If today is Sunday
        days_until_monday = 1
    return start_date + timedelta(days=days_until_monday)


def get_next_weekday(
    default_start_hour: int = 9,
    time_provider: ITimeProvider | None = None,
) -> datetime:
    """Get the next weekday (skip weekends).

    Args:
        default_start_hour: Hour to set for the returned datetime (default: 9)
        time_provider: Provider for current time. Defaults to SystemTimeProvider.

    Returns:
        datetime object representing the next weekday at the specified hour
    """
    provider = _get_time_provider(time_provider)
    today = provider.now()
    next_day = today + timedelta(days=1)

    # Skip weekends - move to next Monday if needed
    while is_weekend(next_day):
        next_day += timedelta(days=1)

    # Set time to specified hour for schedule start times
    return next_day.replace(hour=default_start_hour, minute=0, second=0, microsecond=0)
