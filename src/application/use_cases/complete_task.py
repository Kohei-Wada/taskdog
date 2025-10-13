"""Use case for completing a task."""

from application.dto.complete_task_input import CompleteTaskInput
from application.services.task_status_service import TaskStatusService
from application.use_cases.base import UseCase
from application.validators.validator_registry import TaskFieldValidatorRegistry
from domain.entities.task import Task, TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


class CompleteTaskUseCase(UseCase[CompleteTaskInput, Task]):
    """Use case for completing a task.

    Sets task status to COMPLETED and records actual end time.
    """

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker for recording timestamps
        """
        self.repository = repository
        self.time_tracker = time_tracker
        self.validator_registry = TaskFieldValidatorRegistry(repository)
        self.status_service = TaskStatusService()

    def execute(self, input_dto: CompleteTaskInput) -> Task:
        """Execute task completion.

        Args:
            input_dto: Task completion input data

        Returns:
            Updated task with COMPLETED status

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskNotStartedError: If task is PENDING (not started yet)
            IncompleteChildrenError: If task has incomplete children

        Note:
            Idempotent: Completing an already-finished task returns the task unchanged.
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Validate status transition using validator registry (Clean Architecture)
        # Note: Validator handles idempotency (returns early if already finished)
        self.validator_registry.validate_field("status", TaskStatus.COMPLETED, task)

        # Change status with time tracking
        return self.status_service.change_status_with_tracking(
            task, TaskStatus.COMPLETED, self.time_tracker, self.repository
        )
