"""Registry for field validators."""

from typing import Any

from taskdog_core.application.validators.datetime_validator import DateTimeValidator
from taskdog_core.application.validators.field_validator import FieldValidator
from taskdog_core.application.validators.numeric_field_validator import (
    NumericFieldValidator,
)
from taskdog_core.application.validators.status_validator import StatusValidator
from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.repositories.task_repository import TaskRepository


class TaskFieldValidatorRegistry:
    """Registry for field-specific validators.

    This class manages all field validators and provides a unified interface
    for validating task field updates.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize the validator registry.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository
        self._validators: dict[str, FieldValidator] = {}
        self._register_validators()

    def _register_validators(self) -> None:
        """Register all field validators."""
        self._validators["status"] = StatusValidator()
        self._validators["deadline"] = DateTimeValidator("deadline")
        self._validators["planned_start"] = DateTimeValidator("planned_start")
        self._validators["planned_end"] = DateTimeValidator("planned_end")
        self._validators["estimated_duration"] = NumericFieldValidator(
            "estimated_duration"
        )
        self._validators["priority"] = NumericFieldValidator("priority")

    def validate_field(self, field_name: str, value: Any, task: Task) -> None:
        """Validate a field value if a validator exists for that field.

        Args:
            field_name: Name of the field being updated
            value: New value for the field
            task: Task being updated

        Raises:
            TaskValidationError: If validation fails
        """
        if field_name in self._validators:
            self._validators[field_name].validate(value, task, self.repository)
