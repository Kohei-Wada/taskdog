"""Validator for status field."""

from application.validators.field_validator import FieldValidator
from domain.entities.task import Task, TaskStatus
from domain.services.task_eligibility_checker import TaskEligibilityChecker
from infrastructure.persistence.task_repository import TaskRepository


class StatusValidator(FieldValidator):
    """Validator for status field updates.

    Business Rules:
    - PENDING → COMPLETED transition not allowed (must start first)
    - Cannot complete task with incomplete children
    """

    def validate(self, value: TaskStatus, task: Task, repository: TaskRepository) -> None:
        """Validate status update.

        Args:
            value: New status (TaskStatus enum)
            task: Task being updated
            repository: Repository for data access

        Raises:
            TaskNotStartedError: If PENDING → COMPLETED transition attempted
            IncompleteChildrenError: If task has incomplete children
        """
        # Only validate COMPLETED transitions
        if value != TaskStatus.COMPLETED:
            return

        # Ensure task has ID (from repository)
        assert task.id is not None

        # Use existing business rule from TaskEligibilityChecker
        children = repository.get_children(task.id)
        TaskEligibilityChecker.validate_can_be_completed(task, children)
