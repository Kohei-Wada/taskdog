"""Validator for status field."""

from application.validators.field_validator import FieldValidator
from domain.entities.task import Task, TaskStatus
from domain.services.task_eligibility_checker import TaskEligibilityChecker
from infrastructure.persistence.task_repository import TaskRepository


class StatusValidator(FieldValidator):
    """Validator for status field updates.

    Business Rules:
    - Cannot start task if it has children (must start leaf tasks instead)
    - Cannot start task if it's already finished
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
            TaskWithChildrenError: If trying to start task with children
            TaskAlreadyFinishedError: If trying to start already finished task
            TaskNotStartedError: If PENDING → COMPLETED transition attempted
            IncompleteChildrenError: If task has incomplete children
        """
        # Ensure task has ID (from repository)
        assert task.id is not None

        # Get children for validation
        children = repository.get_children(task.id)

        # Validate based on target status
        if value == TaskStatus.IN_PROGRESS:
            # Use existing business rule from TaskEligibilityChecker
            TaskEligibilityChecker.validate_can_be_started(task, children)
        elif value == TaskStatus.COMPLETED:
            # Idempotency: Skip validation if task is already finished
            # (completing an already-completed task is not an error)
            if task.is_finished:
                return

            # Use existing business rule from TaskEligibilityChecker
            TaskEligibilityChecker.validate_can_be_completed(task, children)
