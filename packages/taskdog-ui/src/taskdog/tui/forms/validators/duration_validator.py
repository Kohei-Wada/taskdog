"""Validator for estimated duration."""

from taskdog.constants.validation_messages import ValidationMessages
from taskdog.tui.forms.validators.base import BaseValidator, ValidationResult


class DurationValidator(BaseValidator):
    """Validator for estimated duration."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate estimated duration in hours.

        Args:
            value: Duration string to validate (can be empty for no estimate)

        Returns:
            ValidationResult with validation status, error message, and parsed duration
        """
        duration_str = value.strip()

        # Empty string means no duration estimate
        if not duration_str:
            return DurationValidator._success(None)

        # Try to parse as float
        try:
            duration = float(duration_str)
        except ValueError:
            return DurationValidator._error(ValidationMessages.DURATION_MUST_BE_NUMBER)

        # Check that it's positive
        if duration <= 0:
            return DurationValidator._error(
                ValidationMessages.DURATION_MUST_BE_POSITIVE
            )

        # Check reasonable upper limit (999 hours)
        if duration > 999:
            return DurationValidator._error(ValidationMessages.DURATION_MAX_EXCEEDED)

        return DurationValidator._success(duration)
