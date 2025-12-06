"""Custom Click DateTime type that adds default time when only date is provided."""

import re
from datetime import datetime, time
from typing import Any

import click

from taskdog.tui.constants.ui_settings import DEFAULT_END_HOUR, DEFAULT_START_HOUR
from taskdog_core.shared.constants.formats import DATETIME_FORMAT


class DateTimeWithDefault(click.DateTime):
    """DateTime parameter type that adds default time when only date is provided.

    Accepts the following formats:
    - YYYY-MM-DD (adds default time)
    - MM-DD (adds current year and default time)
    - MM/DD (adds current year and default time)
    - YYYY-MM-DD HH:MM:SS (uses provided time)

    Args:
        default_hour: Default hour to use when only date is provided.
                     If None, uses business hour default (18 = 6 PM)
                     If "start", uses business hour default (9 = 9 AM)
                     If int, uses that specific hour (0-23)
    """

    def __init__(self, default_hour: int | str | None = None):
        """Initialize with supported datetime formats and default hour.

        Args:
            default_hour: Hour to use as default when only date provided
                         - None: uses business hour default (18 = 6 PM)
                         - "start": uses business hour default (9 = 9 AM)
                         - int (0-23): uses specific hour
        """
        # Only use formats with year to avoid Python 3.13+ deprecation warning
        # MM-DD and MM/DD patterns are handled in convert() before parsing
        super().__init__(formats=[DATETIME_FORMAT, "%Y-%m-%d"])

        # Use UI default constants for date parsing convenience
        # These match the common business hour defaults for better UX
        if default_hour is None:
            self.default_hour = DEFAULT_END_HOUR  # Business day end (6 PM)
        elif default_hour == "start":
            self.default_hour = DEFAULT_START_HOUR  # Business day start (9 AM)
        else:
            self.default_hour = int(default_hour)

    def convert(
        self, value: Any, param: Any, ctx: click.Context | None
    ) -> datetime | None:
        """Convert date string to datetime, adding default time if needed.

        Args:
            value: The date string to convert
            param: The parameter object
            ctx: The Click context

        Returns:
            datetime object, or None if empty

        Raises:
            click.BadParameter: If date format is invalid
        """
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None

        # Strip whitespace from input
        if isinstance(value, str):
            value = value.strip()

        # Check if input contains time component
        has_time = isinstance(value, str) and " " in value

        # Pre-process MM-DD or MM/DD format by adding current year
        # This avoids Python 3.13+ deprecation warning for year-less date parsing
        if isinstance(value, str):
            date_part = value.split()[0]  # Get date part (before any space/time)
            # Match MM-DD or MM/DD pattern (1-2 digit month and day)
            if re.match(r"^\d{1,2}[-/]\d{1,2}$", date_part):
                current_year = datetime.now().year
                # Normalize to hyphen separator
                normalized = date_part.replace("/", "-")
                time_part = value[len(date_part) :].strip()
                value = f"{current_year}-{normalized}"
                if time_part:
                    value = f"{value} {time_part}"

        # Use parent class to parse datetime
        dt = super().convert(value, param, ctx)

        if dt is None:
            return None

        # Type narrowing for mypy
        if not isinstance(dt, datetime):
            raise TypeError(f"Expected datetime object, got {type(dt).__name__}")

        # Only add default time if no time was provided in the input
        if not has_time and dt.time() == time(0, 0, 0):
            # Add default time using configured hour
            dt = datetime.combine(dt.date(), time(self.default_hour, 0, 0))

        # Return datetime object (not string)
        return dt
