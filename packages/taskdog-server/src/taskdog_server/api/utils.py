"""API utility functions."""

from datetime import date

from fastapi import HTTPException, status

from taskdog_core.shared.utils.datetime_parser import (
    parse_iso_date as _parse_iso_date,
)


def parse_iso_date(date_string: str | None) -> date | None:
    """Parse ISO date string to date object.

    Args:
        date_string: ISO format date string (e.g., "2025-01-15")

    Returns:
        Parsed date object, or None if input is None

    Raises:
        HTTPException: 400 if date format is invalid
    """
    try:
        return _parse_iso_date(date_string)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {e}",
        ) from e
