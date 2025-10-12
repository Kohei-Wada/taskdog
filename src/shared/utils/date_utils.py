"""Utilities for parsing datetime strings."""

from datetime import date, datetime

from domain.constants import DATETIME_FORMAT


class DateTimeParser:
    """Utilities for parsing datetime strings."""

    @staticmethod
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

    @staticmethod
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
