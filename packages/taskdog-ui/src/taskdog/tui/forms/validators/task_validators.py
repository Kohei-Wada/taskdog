"""Validators for task name and priority."""

from taskdog.constants.validation_messages import ValidationMessages
from taskdog.tui.forms.validators.base import BaseValidator, ValidationResult


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
            return TaskNameValidator._error(ValidationMessages.TASK_NAME_REQUIRED)
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
            return PriorityValidator._error(ValidationMessages.PRIORITY_MUST_BE_NUMBER)

        # Check that priority is positive
        if priority <= 0:
            return PriorityValidator._error(
                ValidationMessages.PRIORITY_MUST_BE_POSITIVE
            )

        return PriorityValidator._success(priority)
