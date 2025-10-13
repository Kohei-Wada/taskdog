"""Validator for parent_id field."""

from application.validators.field_validator import FieldValidator
from domain.entities.task import Task
from domain.exceptions.task_exceptions import CircularReferenceError, ParentTaskNotFoundError
from infrastructure.persistence.task_repository import TaskRepository


class ParentIdValidator(FieldValidator):
    """Validator for parent_id field updates.

    Business Rules:
    - Parent task must exist
    - No self-reference allowed
    - No circular reference in ancestor chain
    """

    def validate(self, value: int, task: Task, repository: TaskRepository) -> None:
        """Validate parent_id update.

        Args:
            value: New parent_id (int)
            task: Task being updated
            repository: Repository for data access

        Raises:
            CircularReferenceError: If self-reference or circular reference detected
            ParentTaskNotFoundError: If parent doesn't exist
        """
        # Ensure task has ID (from repository)
        assert task.id is not None

        # Check for self-reference
        if value == task.id:
            raise CircularReferenceError("Circular parent reference detected")

        # Check if parent exists
        parent = repository.get_by_id(value)
        if not parent:
            raise ParentTaskNotFoundError(value)

        # Check for circular reference in ancestor chain
        current: Task | None = parent
        while current and current.parent_id is not None:
            if current.parent_id == task.id:
                raise CircularReferenceError("Circular parent reference detected")
            current = repository.get_by_id(current.parent_id)
