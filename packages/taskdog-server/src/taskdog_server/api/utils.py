"""API utility functions."""

from datetime import date, datetime

from fastapi import HTTPException, status


def parse_iso_date(date_string: str | None) -> date | None:
    """Parse ISO date string to date object.

    Args:
        date_string: ISO format date string (e.g., "2025-01-15")

    Returns:
        Parsed date object, or None if input is None

    Raises:
        HTTPException: 400 if date format is invalid
    """
    if not date_string:
        return None
    try:
        return datetime.fromisoformat(date_string).date()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {e}",
        ) from e
