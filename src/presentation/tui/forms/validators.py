"""Common validation logic for TUI forms."""

from dataclasses import dataclass

from dateutil import parser as dateutil_parser


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        is_valid: Whether the validation passed
        error_message: Error message if validation failed (empty if valid)
        value: The validated/parsed value (None if validation failed)
    """

    is_valid: bool
    error_message: str = ""
    value: object = None


class TaskNameValidator:
    """Validator for task names."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate a task name.

        Args:
            value: Task name to validate

        Returns:
            ValidationResult with validation status and error message
        """
        name = value.strip()
        if not name:
            return ValidationResult(
                is_valid=False, error_message="Task name is required", value=None
            )
        return ValidationResult(is_valid=True, error_message="", value=name)


class PriorityValidator:
    """Validator for task priority."""

    DEFAULT_PRIORITY = 5
    MIN_PRIORITY = 1
    MAX_PRIORITY = 10

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate a task priority.

        Args:
            value: Priority value to validate (can be empty for default)

        Returns:
            ValidationResult with validation status, error message, and parsed priority
        """
        priority_str = value.strip()

        # Empty string means default priority
        if not priority_str:
            return ValidationResult(
                is_valid=True,
                error_message="",
                value=PriorityValidator.DEFAULT_PRIORITY,
            )

        # Try to parse as integer
        try:
            priority = int(priority_str)
        except ValueError:
            return ValidationResult(
                is_valid=False, error_message="Priority must be a number", value=None
            )

        # Check range
        if priority < PriorityValidator.MIN_PRIORITY or priority > PriorityValidator.MAX_PRIORITY:
            return ValidationResult(
                is_valid=False,
                error_message=f"Priority must be between {PriorityValidator.MIN_PRIORITY} and {PriorityValidator.MAX_PRIORITY}",
                value=None,
            )

        return ValidationResult(is_valid=True, error_message="", value=priority)


class DeadlineValidator:
    """Validator for task deadlines."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate a task deadline.

        Args:
            value: Deadline string to validate (can be empty for no deadline)

        Returns:
            ValidationResult with validation status, error message, and formatted deadline
        """
        deadline_str = value.strip()

        # Empty string means no deadline
        if not deadline_str:
            return ValidationResult(is_valid=True, error_message="", value=None)

        # Try to parse using dateutil
        try:
            parsed_date = dateutil_parser.parse(deadline_str, fuzzy=True)
            # Convert to the standard format YYYY-MM-DD HH:MM:SS
            formatted_deadline = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            return ValidationResult(is_valid=True, error_message="", value=formatted_deadline)
        except (ValueError, TypeError):
            return ValidationResult(
                is_valid=False,
                error_message="Invalid deadline format. Examples: 2025-12-31, tomorrow 6pm",
                value=None,
            )


class DurationValidator:
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
            return ValidationResult(is_valid=True, error_message="", value=None)

        # Try to parse as float
        try:
            duration = float(duration_str)
        except ValueError:
            return ValidationResult(
                is_valid=False, error_message="Duration must be a number", value=None
            )

        # Check that it's positive
        if duration <= 0:
            return ValidationResult(
                is_valid=False,
                error_message="Duration must be greater than 0",
                value=None,
            )

        # Check reasonable upper limit (999 hours)
        if duration > 999:
            return ValidationResult(
                is_valid=False,
                error_message="Duration must be 999 hours or less",
                value=None,
            )

        return ValidationResult(is_valid=True, error_message="", value=duration)
