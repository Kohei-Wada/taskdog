"""Validator for status field."""

from application.validators.field_validator import FieldValidator
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    IncompleteChildrenError,
    TaskAlreadyFinishedError,
    TaskNotStartedError,
    TaskWithChildrenError,
)
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
            self._validate_can_be_started(task, children)
        elif value == TaskStatus.COMPLETED:
            self._validate_can_be_completed(task, children)

    def _validate_can_be_started(self, task: Task, children: list[Task]) -> None:
        """Validate task can be started.

        Args:
            task: Task to validate
            children: Child tasks of the task

        Raises:
            TaskAlreadyFinishedError: If task is already finished
            TaskWithChildrenError: If task has child tasks

        Business Rules:
            - Cannot start if task is already finished (COMPLETED/FAILED)
            - Cannot start if task has children (must start leaf tasks instead)
        """
        assert task.id is not None

        # Early check: Cannot restart finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task.id, task.status.value)

        # Cannot start if task has children
        if len(children) > 0:
            raise TaskWithChildrenError(task.id, children)

    def _validate_can_be_completed(self, task: Task, children: list[Task]) -> None:
        """Validate task can be completed.

        Args:
            task: Task to validate
            children: Child tasks of the task

        Raises:
            TaskAlreadyFinishedError: If task is already finished
            TaskNotStartedError: If task is PENDING (not started yet)
            IncompleteChildrenError: If task has incomplete children

        Business Rules:
            - Cannot complete if task is already finished (COMPLETED/FAILED)
            - Cannot complete if task is PENDING (must be started first)
            - Cannot complete if task has incomplete children
            - All children must be COMPLETED before parent can be completed
        """
        assert task.id is not None

        # Early check: Cannot re-complete finished tasks
        if task.is_finished:
            raise TaskAlreadyFinishedError(task.id, task.status.value)

        # Cannot complete PENDING tasks (must start first)
        if task.status == TaskStatus.PENDING:
            raise TaskNotStartedError(task.id)

        # Cannot complete if task has incomplete children
        incomplete_children = [c for c in children if c.status != TaskStatus.COMPLETED]
        if len(incomplete_children) > 0:
            raise IncompleteChildrenError(task.id, incomplete_children)
