"""Validator for status field."""

from taskdog_core.application.validators.dependency_validator import DependencyValidator
from taskdog_core.application.validators.field_validator import FieldValidator
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskAlreadyInProgressError,
    TaskNotStartedError,
    TaskValidationError,
)
from taskdog_core.domain.repositories.task_repository import TaskRepository


class StatusValidator(FieldValidator):
    """Validator for status field updates.

    Business Rules:
    - Cannot start task if it's already finished
    - Cannot start task if dependencies are not met (all dependencies must be COMPLETED)
    - PENDING → COMPLETED transition not allowed (must start first)
    - Can pause IN_PROGRESS task back to PENDING
    - Can cancel PENDING or IN_PROGRESS tasks
    - Cannot resume finished tasks (COMPLETED, CANCELED)
    """

    def validate(
        self, value: TaskStatus, task: Task, repository: TaskRepository
    ) -> None:
        # Ensure task.id is non-None and get the validated ID
        task_id = self._get_validated_task_id(task)

        # Validate based on target status
        if value == TaskStatus.IN_PROGRESS:
            self._validate_can_be_started(task, task_id, repository)
        elif value == TaskStatus.COMPLETED:
            self._validate_can_be_completed(task, task_id)
        elif value == TaskStatus.CANCELED:
            self._validate_can_be_canceled(task, task_id)
        elif value == TaskStatus.PENDING:
            self._validate_can_be_paused(task, task_id)

    @staticmethod
    def _get_validated_task_id(task: Task) -> int:
        """Get task ID after validating it is not None.

        This is guaranteed to be true as the validator is only called after
        successful repository.get_by_id() in use cases, but we verify it
        for type safety and early error detection.

        Args:
            task: Task to validate

        Returns:
            The validated task ID (guaranteed to be int, not None)

        Raises:
            TaskValidationError: If task.id is None
        """
        if task.id is None:
            raise TaskValidationError("Task ID must not be None for status validation")
        return task.id

    def _validate_can_be_started(
        self, task: Task, task_id: int, repository: TaskRepository
    ) -> None:
        # Early check: Cannot restart finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task_id, task.status.value, "start")

        # Cannot start a task that is already in progress
        if task.status == TaskStatus.IN_PROGRESS:
            raise TaskAlreadyInProgressError(task_id)

        # Check dependencies: all dependencies must be COMPLETED
        DependencyValidator.validate_dependencies_met(task, repository)

    def _validate_can_be_completed(self, task: Task, task_id: int) -> None:
        # Early check: Cannot re-complete finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task_id, task.status.value, "complete")

        # Cannot complete PENDING tasks (must start first)
        if task.status == TaskStatus.PENDING:
            raise TaskNotStartedError(task_id)

    def _validate_can_be_canceled(self, task: Task, task_id: int) -> None:
        # Cannot cancel already finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task_id, task.status.value, "cancel")

    def _validate_can_be_paused(self, task: Task, task_id: int) -> None:
        # Cannot pause finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task_id, task.status.value, "pause")
