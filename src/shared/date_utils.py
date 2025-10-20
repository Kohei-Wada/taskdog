"""Date utility functions shared across the application."""

from datetime import datetime, timedelta


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
