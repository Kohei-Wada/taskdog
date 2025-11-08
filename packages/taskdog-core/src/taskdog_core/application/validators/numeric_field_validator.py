"""Validator for numeric fields (estimated_duration, priority)."""

from typing import Any

from taskdog_core.application.validators.field_validator import FieldValidator
from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError
from taskdog_core.domain.repositories.task_repository import TaskRepository


class NumericFieldValidator(FieldValidator):
    """Validator for numeric fields that must be positive.

    Business Rules:
        - Value must be greater than 0
        - None is allowed (for clearing the field)
        - Negative values are rejected
        - Zero values are rejected
    """

    def __init__(self, field_name: str):
        """Initialize validator.

        Args:
            field_name: Name of the numeric field being validated
        """
        self.field_name = field_name

    def validate(self, value: Any, task: Task, repository: TaskRepository) -> None:
        """Validate numeric field value.

        Args:
            value: The numeric value to validate
            task: The task being updated (unused)
            repository: Repository for data access (unused)

        Raises:
            TaskValidationError: If value is not positive
        """
        # Skip validation if value is None (clearing the field)
        if value is None:
            return

        # Validate that value is numeric (int or float)
        if not isinstance(value, int | float):
            raise TaskValidationError(
                f"Invalid type for {self.field_name}: {type(value).__name__}. Expected int or float"
            )

        # Reject non-positive values
        if value <= 0:
            raise TaskValidationError(
                f"{self.field_name.replace('_', ' ').capitalize()} must be greater than 0 "
                f"(got {value})"
            )
