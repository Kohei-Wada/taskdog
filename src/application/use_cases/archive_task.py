"""Use case for archiving a task."""

from application.dto.archive_task_request import ArchiveTaskRequest
from application.use_cases.base import UseCase
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskNotFoundException
from domain.repositories.task_repository import TaskRepository


class ArchiveTaskUseCase(UseCase[ArchiveTaskRequest, Task]):
    """Use case for archiving tasks.

    Archives a task for data retention while removing it from active views.
    This use case:
    - Sets is_archived flag to True while preserving the task's status
    - Clears schedule data (daily_allocations)
    - Acts as a soft delete mechanism

    Archived tasks are read-only and excluded from default views.
    Use RestoreTaskUseCase to restore an archived task.
    """

    def __init__(self, repository: TaskRepository) -> None:
        """Initialize use case with repository.

        Args:
            repository: Task repository for persistence
        """
        self.repository = repository

    def execute(self, input_dto: ArchiveTaskRequest) -> Task:
        """Archive a task.

        Args:
            input_dto: Input containing task_id

        Returns:
            Archived task

        Raises:
            TaskNotFoundException: If task does not exist
        """
        # Get task
        task = self.repository.get_by_id(input_dto.task_id)
        if not task:
            raise TaskNotFoundException(input_dto.task_id)

        # Set archived flag
        task.is_archived = True

        # Clear schedule data
        task.daily_allocations = {}

        # Save and return
        self.repository.save(task)
        return task
