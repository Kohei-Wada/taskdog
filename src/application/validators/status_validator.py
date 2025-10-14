"""Validator for status field."""

from application.validators.field_validator import FieldValidator
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotStartedError,
)
from infrastructure.persistence.task_repository import TaskRepository


class StatusValidator(FieldValidator):
    """Validator for status field updates.

    Business Rules:
    - Cannot start task if it's already finished
    - PENDING → COMPLETED transition not allowed (must start first)
    """

    def validate(self, value: TaskStatus, task: Task, repository: TaskRepository) -> None:
        """Validate status update.

        Args:
            value: New status (TaskStatus enum)
            task: Task being updated
            repository: Repository for data access

        Raises:
            TaskAlreadyFinishedError: If trying to start already finished task
            TaskNotStartedError: If PENDING → COMPLETED transition attempted
        """
        # Ensure task has ID (from repository)
        assert task.id is not None

        # Validate based on target status
        if value == TaskStatus.IN_PROGRESS:
            self._validate_can_be_started(task)
        elif value == TaskStatus.COMPLETED:
            self._validate_can_be_completed(task)

    def _validate_can_be_started(self, task: Task) -> None:
        """Validate task can be started.

        Args:
            task: Task to validate

        Raises:
            TaskAlreadyFinishedError: If task is already finished

        Business Rules:
            - Cannot start if task is already finished (COMPLETED/FAILED)
        """
        assert task.id is not None

        # Early check: Cannot restart finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task.id, task.status.value)

    def _validate_can_be_completed(self, task: Task) -> None:
        """Validate task can be completed.

        Args:
            task: Task to validate

        Raises:
            TaskAlreadyFinishedError: If task is already finished
            TaskNotStartedError: If task is PENDING (not started yet)

        Business Rules:
            - Cannot complete if task is already finished (COMPLETED/FAILED)
            - Cannot complete if task is PENDING (must be started first)
        """
        assert task.id is not None

        # Early check: Cannot re-complete finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task.id, task.status.value)

        # Cannot complete PENDING tasks (must start first)
        if task.status == TaskStatus.PENDING:
            raise TaskNotStartedError(task.id)
