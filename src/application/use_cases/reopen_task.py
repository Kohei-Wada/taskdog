"""Use case for reopening a completed or canceled task."""

from application.dto.reopen_task_input import ReopenTaskInput
from application.use_cases.base import UseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    DependencyNotMetError,
    TaskNotFoundException,
    TaskValidationError,
)
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


class ReopenTaskUseCase(UseCase[ReopenTaskInput, Task]):
    """Use case for reopening a completed or canceled task.

    Reopening transitions a task from COMPLETED or CANCELED back to PENDING.
    This validates that all dependencies are still met before reopening.
    """

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker (unused, kept for interface consistency)
        """
        self.repository = repository
        self.time_tracker = time_tracker

    def _validate_can_reopen(self, task: Task) -> None:
        """Validate that task can be reopened.

        Args:
            task: Task to validate

        Raises:
            TaskValidationError: If task is not in a reopenable state
        """
        if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELED):
            raise TaskValidationError(
                f"Cannot reopen task with status {task.status.value}. "
                "Only COMPLETED or CANCELED tasks can be reopened."
            )

        if task.is_deleted:
            raise TaskValidationError(
                "Cannot reopen deleted task. Restore the task first with 'restore' command."
            )

    def _validate_dependencies(self, task: Task) -> None:
        """Validate that all dependencies are met.

        Args:
            task: Task to validate

        Raises:
            DependencyNotMetError: If any dependency is not completed
        """
        if not task.depends_on:
            return  # No dependencies to check

        unmet_dependency_ids = []
        for dep_id in task.depends_on:
            dep_task = self.repository.get_by_id(dep_id)
            if dep_task is None or dep_task.status != TaskStatus.COMPLETED:
                # Dependency doesn't exist or is not completed
                unmet_dependency_ids.append(dep_id)

        if unmet_dependency_ids:
            # task.id should always be set at this point, but mypy needs the assertion
            assert task.id is not None
            raise DependencyNotMetError(
                task_id=task.id,
                unmet_dependencies=unmet_dependency_ids,
            )

    def execute(self, input_dto: ReopenTaskInput) -> Task:
        """Execute task reopening.

        Args:
            input_dto: Reopen task input data

        Returns:
            Updated task with PENDING status

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskValidationError: If task cannot be reopened
            DependencyNotMetError: If dependencies are not met
        """
        # Get task
        task = self.repository.get_by_id(input_dto.task_id)
        if task is None:
            raise TaskNotFoundException(input_dto.task_id)

        # Validate can reopen
        self._validate_can_reopen(task)

        # Validate dependencies
        self._validate_dependencies(task)

        # Clear time tracking (reset timestamps)
        task.actual_start = None
        task.actual_end = None

        # Set status to PENDING
        task.status = TaskStatus.PENDING

        # Save changes
        self.repository.save(task)

        return task
