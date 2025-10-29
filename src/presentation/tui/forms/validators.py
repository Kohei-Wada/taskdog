"""Common validation logic for TUI forms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError


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


class BaseValidator(ABC):
    """Base class for all validators.

    This provides a common interface and helper methods for validation.
    """

    @staticmethod
    @abstractmethod
    def validate(*args: Any, **kwargs: Any) -> ValidationResult:
        """Validate the input value.

        Args:
            *args: Positional arguments for validation
            **kwargs: Keyword arguments for validation

        Returns:
            ValidationResult with validation status and error message
        """
        pass

    @staticmethod
    def _success(value: Any) -> ValidationResult:
        """Create a successful validation result.

        Args:
            value: The validated value

        Returns:
            ValidationResult indicating success
        """
        return ValidationResult(is_valid=True, error_message="", value=value)

    @staticmethod
    def _error(message: str) -> ValidationResult:
        """Create a failed validation result.

        Args:
            message: Error message

        Returns:
            ValidationResult indicating failure
        """
        return ValidationResult(is_valid=False, error_message=message, value=None)


class TaskNameValidator(BaseValidator):
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
            return TaskNameValidator._error("Task name is required")
        return TaskNameValidator._success(name)


class PriorityValidator(BaseValidator):
    """Validator for task priority."""

    @staticmethod
    def validate(value: str, default_priority: int) -> ValidationResult:
        """Validate a task priority.

        Args:
            value: Priority value to validate (can be empty for default)
            default_priority: Default priority to use if value is empty

        Returns:
            ValidationResult with validation status, error message, and parsed priority
        """
        priority_str = value.strip()

        # Empty string means default priority
        if not priority_str:
            return PriorityValidator._success(default_priority)

        # Try to parse as integer
        try:
            priority = int(priority_str)
        except ValueError:
            return PriorityValidator._error("Priority must be a number")

        # Check that priority is positive
        if priority <= 0:
            return PriorityValidator._error("Priority must be greater than 0")

        return PriorityValidator._success(priority)


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
            formatted_datetime = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
            return DateTimeValidator._success(formatted_datetime)
        except (ValueError, TypeError, OverflowError, ParserError):
            return DateTimeValidator._error(
                f"Invalid {field_name} format. Examples: 2025-12-31, tomorrow 6pm"
            )


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
            return DurationValidator._error("Duration must be a number")

        # Check that it's positive
        if duration <= 0:
            return DurationValidator._error("Duration must be greater than 0")

        # Check reasonable upper limit (999 hours)
        if duration > 999:
            return DurationValidator._error("Duration must be 999 hours or less")

        return DurationValidator._success(duration)


class DependenciesValidator(BaseValidator):
    """Validator for task dependencies (comma-separated task IDs)."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate comma-separated task IDs.

        Args:
            value: Comma-separated task IDs (e.g., "1,2,3")

        Returns:
            ValidationResult with validation status, error message, and list of task IDs
        """
        dependencies_str = value.strip()

        # Empty string means no dependencies
        if not dependencies_str:
            return DependenciesValidator._success([])

        # Split by comma and parse each ID
        parts = [p.strip() for p in dependencies_str.split(",")]
        task_ids = []

        for part in parts:
            if not part:  # Skip empty parts
                continue

            try:
                task_id = int(part)
            except ValueError:
                return DependenciesValidator._error(f"Invalid task ID: '{part}'. Must be a number.")

            if task_id <= 0:
                return DependenciesValidator._error(f"Task ID must be positive: {task_id}")

            task_ids.append(task_id)

        # Remove duplicates while preserving order
        unique_ids = list(dict.fromkeys(task_ids))

        return DependenciesValidator._success(unique_ids)


class TagsValidator(BaseValidator):
    """Validator for task tags (comma-separated strings)."""

    @staticmethod
    def validate(value: str) -> ValidationResult:
        """Validate comma-separated tags.

        Args:
            value: Comma-separated tags (e.g., "work,urgent,client-a")

        Returns:
            ValidationResult with validation status, error message, and list of tags
        """
        tags_str = value.strip()

        # Empty string means no tags
        if not tags_str:
            return TagsValidator._success([])

        # Split by comma and parse each tag
        parts = [p.strip() for p in tags_str.split(",")]
        tags = []

        for part in parts:
            if not part:  # Skip empty parts
                continue

            # Check for empty tag
            if not part.strip():
                return TagsValidator._error("Tag cannot be empty")

            tags.append(part)

        # Check for duplicates
        if len(tags) != len(set(tags)):
            return TagsValidator._error("Tags must be unique")

        return TagsValidator._success(tags)
