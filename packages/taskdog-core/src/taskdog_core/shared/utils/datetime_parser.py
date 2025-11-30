"""ISO 8601 datetime parsing and formatting utilities.

This module provides utilities for parsing and formatting ISO 8601 datetime strings.
Used by API server and UI for consistent datetime handling across the monorepo.

Note: For internal storage format ("%Y-%m-%d %H:%M:%S"), use date_utils.py instead.

Error Handling:
- Returns None for None/empty input
- Raises ValueError for malformed input (consumers handle translation)
"""

from datetime import date, datetime


def parse_iso_date(date_str: str | None) -> date | None:
    """Parse ISO 8601 date string to date object.

    Supports formats: "2025-01-15", "2025-01-15T10:30:00"

    Args:
        date_str: ISO format date string or None

    Returns:
        Parsed date object, or None if input is None/empty

    Raises:
        ValueError: If date_str is present but malformed
    """
    if not date_str:
        return None
    return datetime.fromisoformat(date_str).date()


def parse_iso_datetime(datetime_str: str | None) -> datetime | None:
    """Parse ISO 8601 datetime string to datetime object.

    Args:
        datetime_str: ISO format datetime string or None

    Returns:
        Parsed datetime object, or None if input is None/empty

    Raises:
        ValueError: If datetime_str is present but malformed
    """
    if not datetime_str:
        return None
    return datetime.fromisoformat(datetime_str)


def format_iso_datetime(dt: datetime | None) -> str | None:
    """Format datetime object to ISO 8601 string.

    Args:
        dt: Datetime object or None

    Returns:
        ISO format string, or None if input is None
    """
    if dt is None:
        return None
    return dt.isoformat()


def format_iso_date(d: date | None) -> str | None:
    """Format date object to ISO 8601 string.

    Args:
        d: Date object or None

    Returns:
        ISO format string (YYYY-MM-DD), or None if input is None
    """
    if d is None:
        return None
    return d.isoformat()
