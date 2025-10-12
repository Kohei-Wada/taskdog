"""Custom Click DateTime type that adds default time when only date is provided."""

from datetime import datetime, time

import click

from domain.constants import DATETIME_FORMAT


class DateTimeWithDefault(click.DateTime):
    """DateTime parameter type that adds default time (18:00:00) when only date is provided.

    Accepts the following formats:
    - YYYY-MM-DD (adds default time 18:00:00)
    - MM-DD (adds current year and default time 18:00:00)
    - YYYY-MM-DD HH:MM:SS (uses provided time)
    """

    def __init__(self):
        """Initialize with supported datetime formats."""
        super().__init__(formats=[DATETIME_FORMAT, "%Y-%m-%d", "%m-%d"])

    def convert(self, value, param, ctx):
        """Convert date string to datetime, adding default time if needed.

        Args:
            value: The date string to convert
            param: The parameter object
            ctx: The Click context

        Returns:
            Formatted datetime string (YYYY-MM-DD HH:MM:SS), or None if empty

        Raises:
            click.BadParameter: If date format is invalid
        """
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None

        # Strip whitespace from input
        if isinstance(value, str):
            value = value.strip()

        # Check if input is in MM-DD format (no year provided)
        is_short_format = isinstance(value, str) and len(value.split()[0].split("-")) == 2

        # Check if input contains time component
        has_time = isinstance(value, str) and " " in value

        # Use parent class to parse datetime
        dt = super().convert(value, param, ctx)

        if dt is None:
            return None

        # If MM-DD format was used, add current year
        if is_short_format:
            current_year = datetime.now().year
            dt = dt.replace(year=current_year)

        # Only add default time if no time was provided in the input
        if not has_time and dt.time() == time(0, 0, 0):
            # Add default time 18:00:00
            dt = datetime.combine(dt.date(), time(18, 0, 0))

        # Return formatted string
        return dt.strftime(DATETIME_FORMAT)
