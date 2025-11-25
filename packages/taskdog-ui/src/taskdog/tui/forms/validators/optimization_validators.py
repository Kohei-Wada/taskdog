"""Validators for optimization-related fields."""

from datetime import datetime

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError
from textual.validation import ValidationResult, Validator


class StartDateTextualValidator(Validator):
    """Textual-compatible validator for start date field with fuzzy parsing."""

    def validate(self, value: str) -> ValidationResult:
        """Validate start date input.

        Args:
            value: Input value to validate (required)

        Returns:
            ValidationResult indicating success or failure
        """
        value = value.strip()
        if not value:
            return self.failure("Start date is required")

        try:
            dateutil_parser.parse(value, fuzzy=True)
            return self.success()
        except (ValueError, TypeError, OverflowError, ParserError):
            return self.failure(
                "Invalid date format. Examples: today, tomorrow, 2025-12-01"
            )

    def parse(self, value: str) -> datetime:
        """Parse start date string to datetime.

        Args:
            value: Date string to parse

        Returns:
            Parsed datetime object
        """
        result: datetime = dateutil_parser.parse(value.strip(), fuzzy=True)
        return result
