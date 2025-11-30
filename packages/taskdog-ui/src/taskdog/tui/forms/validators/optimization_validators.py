"""Validators for optimization-related fields."""

from datetime import datetime, timedelta

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError
from textual.validation import ValidationResult, Validator


class StartDateTextualValidator(Validator):
    """Textual-compatible validator for start date field with fuzzy parsing."""

    def _normalize_date_string(self, value: str) -> str:
        """Normalize relative date keywords to actual dates.

        Args:
            value: Date string that may contain relative keywords

        Returns:
            Normalized date string (YYYY-MM-DD format for keywords, original otherwise)
        """
        lower = value.lower()
        today = datetime.now()

        if lower == "today":
            return today.strftime("%Y-%m-%d")
        elif lower == "tomorrow":
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif lower == "yesterday":
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        return value

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
            normalized = self._normalize_date_string(value)
            dateutil_parser.parse(normalized, fuzzy=True)
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
        normalized = self._normalize_date_string(value.strip())
        result: datetime = dateutil_parser.parse(normalized, fuzzy=True)
        return result
