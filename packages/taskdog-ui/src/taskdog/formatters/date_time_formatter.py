"""Date and time formatting utilities."""

from datetime import date, datetime

from taskdog_core.shared.constants.formats import DATETIME_FORMAT


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
    def format_created(created_at: datetime) -> str:
        """Format created timestamp (always shows full datetime).

        Args:
            created_at: Created timestamp

        Returns:
            Formatted timestamp string (YYYY-MM-DD HH:MM:SS)
        """
        return created_at.strftime(DATETIME_FORMAT)

    @staticmethod
    def format_updated(updated_at: datetime) -> str:
        """Format updated timestamp (always shows full datetime).

        Args:
            updated_at: Updated timestamp

        Returns:
            Formatted timestamp string (YYYY-MM-DD HH:MM:SS)
        """
        return updated_at.strftime(DATETIME_FORMAT)

    @staticmethod
    def format_current_timestamp() -> str:
        """Format current timestamp for logging/notes.

        Returns:
            Current timestamp formatted as YYYY-MM-DD HH:MM:SS
        """
        return datetime.now().strftime(DATETIME_FORMAT)

    @staticmethod
    def format_date_only(dt: datetime | date | None) -> str:
        """Format as date only (YYYY-MM-DD).

        Args:
            dt: Datetime or date to format, or None

        Returns:
            Formatted date string, or "-" if dt is None
        """
        if not dt:
            return "-"
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def format_date_for_filename() -> str:
        """Format current date for filename (YYYYMMDD).

        Returns:
            Current date formatted as YYYYMMDD
        """
        return datetime.now().strftime("%Y%m%d")

    @staticmethod
    def format_datetime_for_export(dt: datetime | None) -> str:
        """Format datetime for export (CSV/Markdown).

        Args:
            dt: Datetime to format, or None

        Returns:
            Formatted datetime string, or "-" if dt is None
        """
        if not dt:
            return "-"
        return dt.strftime(DATETIME_FORMAT)

    @staticmethod
    def format_datetime_compact(dt: datetime | None) -> str:
        """Format datetime without seconds (YYYY-MM-DD HH:MM).

        Args:
            dt: Datetime to format, or None

        Returns:
            Formatted datetime string, or "-" if dt is None
        """
        if not dt:
            return "-"
        return dt.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def format_datetime_full(dt: datetime | None) -> str:
        """Format datetime with full format (YYYY-MM-DD HH:MM:SS).

        Alias for format_datetime_for_export for consistency.

        Args:
            dt: Datetime to format, or None

        Returns:
            Formatted datetime string, or "-" if dt is None
        """
        return DateTimeFormatter.format_datetime_for_export(dt)
