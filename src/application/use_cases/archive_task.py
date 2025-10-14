"""Use case for archiving a task."""

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.base import UseCase
from domain.entities.task import TaskStatus
from infrastructure.persistence.task_repository import TaskRepository


class ArchiveTaskUseCase(UseCase[ArchiveTaskInput, None]):
    """Use case for archiving tasks."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: ArchiveTaskInput) -> None:
        """Execute task archiving.

        Args:
            input_dto: Task archiving input data

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)
        task.status = TaskStatus.ARCHIVED
        # Clear schedule data as archived tasks are no longer in active planning
        task.daily_allocations = {}
        self.repository.save(task)
