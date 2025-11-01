"""DateTime field validator."""

from datetime import datetime
from typing import Any

from application.validators.field_validator import FieldValidator
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskValidationError
from domain.repositories.task_repository import TaskRepository


class DateTimeValidator(FieldValidator):
    """Validator for datetime fields (deadline, planned_start, planned_end).

    Business Rules:
        - Future dates are always allowed
        - Past dates are allowed only if task has already started (has actual_start)
        - This allows fixing/updating already-started tasks while preventing
          nonsensical schedules for new tasks
    """

    def __init__(self, field_name: str):
        """Initialize validator.

        Args:
            field_name: Name of the datetime field being validated
        """
        self.field_name = field_name

    def validate(self, value: Any, task: Task, repository: TaskRepository) -> None:
        """Validate datetime field value.

        Args:
            value: The datetime object to validate
            task: The task being updated
            repository: Repository for data access (unused)

        Raises:
            TaskValidationError: If datetime is in the past and task hasn't started
        """
        # Skip validation if value is None (clearing the field)
        if value is None:
            return

        # Validate that value is a datetime object
        if not isinstance(value, datetime):
            raise TaskValidationError(
                f"Invalid datetime type for {self.field_name}: {type(value).__name__}. "
                f"Expected datetime object"
            )

        # Get current time
        now = datetime.now()

        # Allow past dates if task has already started
        if task.actual_start is not None:
            return

        # Reject past dates for tasks that haven't started
        if value < now:
            raise TaskValidationError(
                f"Cannot set {self.field_name} to past date: {value.isoformat()}. "
                f"Tasks that haven't started must have future dates."
            )
