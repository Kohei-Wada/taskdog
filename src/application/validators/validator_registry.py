"""Registry for field validators."""

from typing import Any

from application.validators.deadline_validator import DeadlineValidator
from application.validators.estimated_duration_validator import EstimatedDurationValidator
from application.validators.field_validator import FieldValidator
from application.validators.parent_id_validator import ParentIdValidator
from application.validators.status_validator import StatusValidator
from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository


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
        self._validators["parent_id"] = ParentIdValidator()
        self._validators["estimated_duration"] = EstimatedDurationValidator()
        self._validators["status"] = StatusValidator()
        self._validators["deadline"] = DeadlineValidator()

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

    def has_validator(self, field_name: str) -> bool:
        """Check if a validator exists for the given field.

        Args:
            field_name: Name of the field to check

        Returns:
            True if validator exists, False otherwise
        """
        return field_name in self._validators
