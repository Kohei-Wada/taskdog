"""Validator for date/time fields."""

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError

from taskdog.constants.validation_messages import ValidationMessages
from taskdog.tui.forms.validators.base import BaseValidator, ValidationResult
from taskdog_core.shared.constants.formats import DATETIME_FORMAT


class DateTimeValidator(BaseValidator):
    """Generic validator for date/time fields."""

    @staticmethod
    def validate(value: str, field_name: str, default_hour: int) -> ValidationResult:
        """Validate a date/time string.

        Args:
            value: Date/time string to validate (can be empty for no value)
            field_name: Name of the field for error messages
            default_hour: Default hour to use when only date is provided (from config)

        Returns:
            ValidationResult with validation status, error_message, and formatted date/time
        """
        datetime_str = value.strip()

        # Empty string means no value
        if not datetime_str:
            return DateTimeValidator._success(None)

        # Check if input contains time component (look for colon)
        has_time = ":" in datetime_str

        # Try to parse using dateutil
        try:
            parsed_date = dateutil_parser.parse(datetime_str, fuzzy=True)

            # If no time was provided and parsed time is midnight, apply default hour
            if not has_time and parsed_date.hour == 0 and parsed_date.minute == 0:
                parsed_date = parsed_date.replace(hour=default_hour, minute=0, second=0)

            # Convert to the standard format YYYY-MM-DD HH:MM:SS
            formatted_datetime = parsed_date.strftime(DATETIME_FORMAT)
            return DateTimeValidator._success(formatted_datetime)
        except (ValueError, TypeError, OverflowError, ParserError):
            return DateTimeValidator._error(
                ValidationMessages.invalid_date_format(
                    field_name, "2025-12-31, tomorrow 6pm"
                )
            )
