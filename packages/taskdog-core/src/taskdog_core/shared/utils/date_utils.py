"""Date and time utility functions for task scheduling.

This module provides utilities for:
- Weekday detection (is_weekday)
- Workday calculations (count_weekdays)

Note: Monday=0, Tuesday=1, ..., Friday=4, Saturday=5, Sunday=6
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from taskdog_core.shared.constants import WEEKDAY_THRESHOLD


def is_weekday(dt: datetime | date) -> bool:
    """Check if a date is a weekday (Monday-Friday).

    Args:
        dt: Date or datetime to check

    Returns:
        True if Monday-Friday, False if Saturday-Sunday
    """
    return dt.weekday() < WEEKDAY_THRESHOLD


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
