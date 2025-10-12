"""Custom Click DateTime type that adds default time when only date is provided."""

from datetime import datetime, time

import click

from domain.constants import DATETIME_FORMAT, DEFAULT_END_HOUR


class DateTimeWithDefault(click.DateTime):
    """DateTime parameter type that adds default time when only date is provided.

    Accepts the following formats:
    - YYYY-MM-DD (adds default time)
    - MM-DD (adds current year and default time)
    - MM/DD (adds current year and default time)
    - YYYY-MM-DD HH:MM:SS (uses provided time)

    Args:
        default_hour: Default hour to use when only date is provided (default: 18 for end times)
    """

    def __init__(self, default_hour=DEFAULT_END_HOUR):
        """Initialize with supported datetime formats and default hour.

        Args:
            default_hour: Hour to use as default when only date provided (0-23)
                         Defaults to DEFAULT_END_HOUR (18) for end times/deadlines
        """
        super().__init__(formats=[DATETIME_FORMAT, "%Y-%m-%d", "%m-%d", "%m/%d"])
        self.default_hour = default_hour

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

        # Check if input is in MM-DD or MM/DD format (no year provided)
        if isinstance(value, str):
            date_part = value.split()[0]  # Get date part (before any space/time)
            # Check if it's 2-part date (MM-DD or MM/DD)
            is_short_format = len(date_part.split("-")) == 2 or len(date_part.split("/")) == 2
        else:
            is_short_format = False

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
            # Add default time using configured hour
            dt = datetime.combine(dt.date(), time(self.default_hour, 0, 0))

        # Return formatted string
        return dt.strftime(DATETIME_FORMAT)
