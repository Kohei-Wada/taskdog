"""Base use case for status change operations using Template Method Pattern."""

from abc import ABC, abstractmethod

from application.dto.status_change_input import StatusChangeInput
from application.services.task_status_service import TaskStatusService
from application.use_cases.base import UseCase
from application.validators.validator_registry import TaskFieldValidatorRegistry
from domain.entities.task import Task, TaskStatus
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker


class StatusChangeUseCase[TInput: StatusChangeInput](UseCase[TInput, Task], ABC):
    """Base use case for status change operations.

    This class implements the Template Method pattern to eliminate code duplication
    across status change operations (Start, Complete, Archive, etc.).

    The template method `execute()` defines the common workflow:
    1. Get task from repository
    2. Pre-processing hook (optional)
    3. Get target status (subclass-defined)
    4. Validate status transition (optional)
    5. Apply status change with time tracking
    6. Post-processing hook (optional)
    7. Return updated task

    Subclasses only need to implement `_get_target_status()` and optionally
    override hooks for custom behavior.

    Example:
        class StartTaskUseCase(StatusChangeUseCase[StartTaskInput]):
            def _get_target_status(self) -> TaskStatus:
                return TaskStatus.IN_PROGRESS
    """

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker):
        """Initialize use case with common dependencies.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker for recording timestamps
        """
        self.repository = repository
        self.time_tracker = time_tracker
        self.validator_registry = TaskFieldValidatorRegistry(repository)
        self.status_service = TaskStatusService()

    def execute(self, input_dto: TInput) -> Task:
        """Execute status change workflow (Template Method).

        This method defines the common workflow for all status changes.
        Subclasses customize behavior by overriding hooks.

        Args:
            input_dto: Input data containing task_id

        Returns:
            Updated task with new status

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskValidationError: If validation fails
        """
        # 1. Get task from repository
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # 2. Pre-processing hook (optional)
        self._before_status_change(task)

        # 3. Get target status (subclass-defined)
        new_status = self._get_target_status()

        # 4. Validate status transition (optional)
        if self._should_validate():
            self.validator_registry.validate_field("status", new_status, task)

        # 5. Apply status change with time tracking
        task = self.status_service.change_status_with_tracking(
            task, new_status, self.time_tracker, self.repository
        )

        # 6. Post-processing hook (optional)
        self._after_status_change(task)

        return task

    @abstractmethod
    def _get_target_status(self) -> TaskStatus:
        """Return the target status for this use case.

        Subclasses must implement this to specify which status to transition to.

        Returns:
            The target TaskStatus (e.g., IN_PROGRESS, COMPLETED, CANCELED)
        """
        pass

    def _should_validate(self) -> bool:
        """Determine if validation should be performed.

        Override this to disable validation for specific use cases.
        Default behavior is to validate all status transitions.

        Returns:
            True if validation should be performed, False otherwise
        """
        return True

    def _before_status_change(self, task: Task) -> None:
        """Hook for pre-processing before status change.

        Override this to perform custom logic before changing status.
        For example: clearing schedules, checking prerequisites, etc.

        Args:
            task: Task that will be updated
        """
        pass

    def _after_status_change(self, task: Task) -> None:
        """Hook for post-processing after status change.

        Override this to perform custom logic after changing status.
        For example: sending notifications, updating related tasks, etc.

        Args:
            task: Task that was updated
        """
        pass
