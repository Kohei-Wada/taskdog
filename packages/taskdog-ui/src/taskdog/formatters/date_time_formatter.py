"""Date and time formatting utilities."""

from datetime import datetime


class DateTimeFormatter:
    """Formats datetime objects for display in the UI.

    Provides year-aware formatting:
    - Current year: MM-DD HH:MM
    - Other years: 'YY MM-DD HH:MM
    """

    @staticmethod
    def format_datetime(dt: datetime | None, show_year: bool | None = None) -> str:
        """Format datetime for display with year-aware formatting.

        Shows MM-DD HH:MM for current year, 'YY MM-DD HH:MM otherwise.

        Args:
            dt: Datetime to format, or None
            show_year: Override year display. If None, uses year-aware logic.

        Returns:
            Formatted string, or "-" if dt is None
        """
        if not dt:
            return "-"

        if show_year is None:
            show_year = dt.year != datetime.now().year

        if show_year:
            return dt.strftime("'%y %m-%d %H:%M")
        return dt.strftime("%m-%d %H:%M")

    @staticmethod
    def format_deadline(deadline: datetime | None) -> str:
        """Format deadline for display.

        Args:
            deadline: Deadline datetime object or None

        Returns:
            Formatted deadline string
        """
        return DateTimeFormatter.format_datetime(deadline)

    @staticmethod
    def format_planned_start(planned_start: datetime | None) -> str:
        """Format planned start datetime for display.

        Args:
            planned_start: Planned start datetime object or None

        Returns:
            Formatted planned start string
        """
        return DateTimeFormatter.format_datetime(planned_start)

    @staticmethod
    def format_planned_end(planned_end: datetime | None) -> str:
        """Format planned end datetime for display.

        Args:
            planned_end: Planned end datetime object or None

        Returns:
            Formatted planned end string
        """
        return DateTimeFormatter.format_datetime(planned_end)

    @staticmethod
    def format_actual_start(actual_start: datetime | None) -> str:
        """Format actual start datetime for display.

        Args:
            actual_start: Actual start datetime object or None

        Returns:
            Formatted actual start string
        """
        return DateTimeFormatter.format_datetime(actual_start)

    @staticmethod
    def format_actual_end(actual_end: datetime | None) -> str:
        """Format actual end datetime for display.

        Args:
            actual_end: Actual end datetime object or None

        Returns:
            Formatted actual end string
        """
        return DateTimeFormatter.format_datetime(actual_end)

    @staticmethod
    def should_show_year(dt: datetime) -> bool:
        """Check if year should be displayed for a given datetime.

        Args:
            dt: Datetime to check

        Returns:
            True if year should be shown, False otherwise
        """
        return dt.year != datetime.now().year
