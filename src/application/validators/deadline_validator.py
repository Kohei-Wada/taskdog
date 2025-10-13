"""Validator for deadline field."""

from application.validators.field_validator import FieldValidator
from domain.entities.task import Task
from domain.exceptions.task_exceptions import DeadlineAfterParentError
from infrastructure.persistence.task_repository import TaskRepository


class DeadlineValidator(FieldValidator):
    """Validator for deadline field updates.

    Business Rules:
    - Child task deadline must not be after parent task deadline
    - Ensures hierarchy consistency in project planning
    """

    def validate(self, value: str, task: Task, repository: TaskRepository) -> None:
        """Validate deadline update.

        Args:
            value: New deadline (datetime string, format: YYYY-MM-DD HH:MM:SS)
            task: Task being updated
            repository: Repository for data access

        Raises:
            DeadlineAfterParentError: If deadline is after parent's deadline
        """
        # Ensure task has ID (from repository)
        assert task.id is not None

        # Only validate if task has a parent
        if task.parent_id is None:
            return

        # Get parent task
        parent = repository.get_by_id(task.parent_id)
        if parent is None or parent.deadline is None:
            return

        # Compare deadlines (string comparison works for ISO format)
        if value > parent.deadline:
            raise DeadlineAfterParentError(task.id, task.parent_id, value, parent.deadline)
