"""ISO 8601 datetime parsing and formatting utilities.

This module provides utilities for parsing and formatting ISO 8601 datetime strings.
Used by API server and UI for consistent datetime handling across the monorepo.

Note: For internal storage format ("%Y-%m-%d %H:%M:%S"), use date_utils.py instead.

Error Handling:
- Returns None for None/empty input
- Raises ValueError for malformed input (consumers handle translation)
"""

from collections.abc import Iterable
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


def parse_date_set(date_strings: Iterable[str]) -> set[date]:
    """Parse iterable of ISO date strings to set of date objects.

    Args:
        date_strings: Iterable of ISO date strings

    Returns:
        Set of date objects

    Raises:
        ValueError: If any date string is malformed or empty
    """
    result: set[date] = set()
    for date_str in date_strings:
        if not date_str:
            raise ValueError("Empty date string")
        result.add(datetime.fromisoformat(date_str).date())
    return result


def parse_date_dict[T](str_dict: dict[str, T]) -> dict[date, T]:
    """Parse dictionary with ISO date string keys to date object keys.

    Args:
        str_dict: Dictionary with ISO date string keys

    Returns:
        Dictionary with date object keys

    Raises:
        ValueError: If any date key is malformed
    """
    if not str_dict:
        return {}
    return {datetime.fromisoformat(k).date(): v for k, v in str_dict.items()}


def format_date_dict[T](date_dict: dict[date, T]) -> dict[str, T]:
    """Format dictionary with date keys to ISO string keys.

    Args:
        date_dict: Dictionary with date object keys

    Returns:
        Dictionary with ISO date string keys
    """
    if not date_dict:
        return {}
    return {k.isoformat(): v for k, v in date_dict.items()}
