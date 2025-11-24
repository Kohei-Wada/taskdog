"""Validators for optimization-related fields."""

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError

from taskdog.tui.constants.ui_settings import MAX_HOURS_PER_DAY
from taskdog.tui.forms.validators.base import BaseValidator, ValidationResult


class MaxHoursValidator(BaseValidator):
    """Validator for max hours per day field."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate and parse max hours input.

        Args:
            value: Input value to validate (can be empty for server default)

        Returns:
            ValidationResult with validation status and parsed float value.
            Empty value is allowed - server will apply config default.
        """
        if not value:
            # Empty value is allowed - server will apply config default
            return MaxHoursValidator._success(None)

        try:
            hours = float(value)
            if hours <= 0:
                return MaxHoursValidator._error("Max hours must be greater than 0")
            if hours > MAX_HOURS_PER_DAY:
                return MaxHoursValidator._error(
                    f"Max hours cannot exceed {MAX_HOURS_PER_DAY}"
                )
            return MaxHoursValidator._success(hours)
        except ValueError:
            return MaxHoursValidator._error("Max hours must be a valid number")


class StartDateValidator(BaseValidator):
    """Validator for optimization start date field."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate and parse start date input.

        Args:
            value: Input value to validate (required)

        Returns:
            ValidationResult with validation status and parsed datetime value.
        """
        if not value:
            return StartDateValidator._error("Start date is required")

        try:
            parsed_date = dateutil_parser.parse(value, fuzzy=True)
            return StartDateValidator._success(parsed_date)
        except (ValueError, TypeError, OverflowError, ParserError):
            return StartDateValidator._error(
                "Invalid date format. Examples: today, tomorrow, 2025-12-01"
            )
