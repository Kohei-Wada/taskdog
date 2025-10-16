"""Use case for archiving a task."""

from application.dto.archive_task_input import ArchiveTaskInput
from application.services.task_status_service import TaskStatusService
from application.use_cases.base import UseCase
from domain.entities.task import TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


class ArchiveTaskUseCase(UseCase[ArchiveTaskInput, None]):
    """Use case for archiving tasks."""

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker for recording timestamps
        """
        self.repository = repository
        self.time_tracker = time_tracker
        self.status_service = TaskStatusService()

    def execute(self, input_dto: ArchiveTaskInput) -> None:
        """Execute task archiving.

        Args:
            input_dto: Task archiving input data

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Clear schedule data as archived tasks are no longer in active planning
        task.daily_allocations = {}

        # Change status with time tracking using TaskStatusService for consistency
        self.status_service.change_status_with_tracking(
            task, TaskStatus.ARCHIVED, self.time_tracker, self.repository
        )
