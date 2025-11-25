"""Validator for date/time fields."""

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError
from textual.validation import ValidationResult, Validator

from taskdog_core.shared.constants.formats import DATETIME_FORMAT


class DateTimeValidator(Validator):
    """Textual-compatible validator for date/time fields with fuzzy parsing."""

    def __init__(self, field_name: str, default_hour: int) -> None:
        """Initialize the validator.

        Args:
            field_name: Name of the field for error messages
            default_hour: Default hour to use when only date is provided
        """
        super().__init__()
        self.field_name = field_name
        self.default_hour = default_hour

    def validate(self, value: str) -> ValidationResult:
        """Validate a date/time string.

        Args:
            value: Date/time string to validate (can be empty for no value)

        Returns:
            ValidationResult indicating success or failure
        """
        datetime_str = value.strip()

        # Empty string is valid (optional field)
        if not datetime_str:
            return self.success()

        # Check if input contains time component (look for colon)
        has_time = ":" in datetime_str

        # Try to parse using dateutil
        try:
            parsed_date = dateutil_parser.parse(datetime_str, fuzzy=True)

            # If no time was provided and parsed time is midnight, apply default hour
            if not has_time and parsed_date.hour == 0 and parsed_date.minute == 0:
                parsed_date = parsed_date.replace(
                    hour=self.default_hour, minute=0, second=0
                )

            # Validate successful - the actual parsing for form submission
            # will be done separately
            return self.success()
        except (ValueError, TypeError, OverflowError, ParserError):
            return self.failure(
                f"Invalid {self.field_name} format. Examples: 2025-12-31, tomorrow 6pm"
            )

    def parse(self, value: str) -> str | None:
        """Parse datetime string to formatted string.

        Args:
            value: Date/time string to parse

        Returns:
            Formatted datetime string (YYYY-MM-DD HH:MM:SS) or None if empty
        """
        datetime_str = value.strip()
        if not datetime_str:
            return None

        has_time = ":" in datetime_str
        parsed_date = dateutil_parser.parse(datetime_str, fuzzy=True)

        if not has_time and parsed_date.hour == 0 and parsed_date.minute == 0:
            parsed_date = parsed_date.replace(
                hour=self.default_hour, minute=0, second=0
            )

        return str(parsed_date.strftime(DATETIME_FORMAT))
