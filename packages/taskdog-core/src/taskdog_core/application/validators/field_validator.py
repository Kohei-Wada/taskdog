"""Abstract base class for field validators."""

from abc import ABC, abstractmethod
from typing import Any

from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.repositories.task_repository import TaskRepository


class FieldValidator(ABC):
    """Abstract base class for field-specific validators.

    Each validator is responsible for validating updates to a specific field,
    including business rules and data integrity constraints.
    """

    @abstractmethod
    def validate(self, value: Any, task: Task, repository: TaskRepository) -> None:
        """Validate a field value for the given task.

        Args:
            value: The new value to validate
            task: The task being updated
            repository: Repository for data access (if needed)

        Raises:
            TaskValidationError: If validation fails
        """
        pass
