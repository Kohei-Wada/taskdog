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
    - Can pause IN_PROGRESS task back to PENDING
    - Cannot resume finished tasks (COMPLETED, FAILED, ARCHIVED)
    """

    def validate(self, value: TaskStatus, task: Task, repository: TaskRepository) -> None:
        # Validate based on target status
        if value == TaskStatus.IN_PROGRESS:
            self._validate_can_be_started(task)
        elif value == TaskStatus.COMPLETED:
            self._validate_can_be_completed(task)
        elif value == TaskStatus.PENDING:
            self._validate_can_be_paused(task)

    def _validate_can_be_started(self, task: Task) -> None:
        # task.id is guaranteed non-None as validator is only called after
        # successful repository.get_by_id() in use cases
        assert task.id is not None

        # Early check: Cannot restart finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task.id, task.status.value)

    def _validate_can_be_completed(self, task: Task) -> None:
        # task.id is guaranteed non-None as validator is only called after
        # successful repository.get_by_id() in use cases
        assert task.id is not None

        # Early check: Cannot re-complete finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task.id, task.status.value)

        # Cannot complete PENDING tasks (must start first)
        if task.status == TaskStatus.PENDING:
            raise TaskNotStartedError(task.id)

    def _validate_can_be_paused(self, task: Task) -> None:
        # task.id is guaranteed non-None as validator is only called after
        # successful repository.get_by_id() in use cases
        assert task.id is not None

        # Cannot pause finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task.id, task.status.value)
