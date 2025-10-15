"""Use case for starting a task."""

from application.dto.start_task_input import StartTaskInput
from application.services.task_status_service import TaskStatusService
from application.use_cases.base import UseCase
from application.validators.validator_registry import TaskFieldValidatorRegistry
from domain.entities.task import Task, TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


class StartTaskUseCase(UseCase[StartTaskInput, Task]):
    """Use case for starting a task.

    Sets task status to IN_PROGRESS and records actual start time.
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

    def execute(self, input_dto: StartTaskInput) -> Task:
        """Execute task start.

        Args:
            input_dto: Task start input data

        Returns:
            Updated task with IN_PROGRESS status

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskAlreadyFinishedError: If task is already finished
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Validate status transition using validator registry (Clean Architecture)
        self.validator_registry.validate_field("status", TaskStatus.IN_PROGRESS, task)

        # Change status with time tracking
        task = self.status_service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )

        return task
