"""Use case for archiving (soft deleting) a task."""

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.base import UseCase
from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository


class ArchiveTaskUseCase(UseCase[ArchiveTaskInput, Task]):
    """Use case for archiving (soft deleting) tasks.

    Archives a task for data retention while removing it from active views.
    This use case:
    - Sets is_deleted flag to True
    - Clears schedule data (daily_allocations)
    - Archiving is always allowed regardless of current status
    """

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def execute(self, input_dto: ArchiveTaskInput) -> Task:
        """Archive (soft delete) a task.

        Args:
            input_dto: ArchiveTaskInput containing task_id

        Returns:
            The archived task

        Raises:
            TaskNotFoundException: If task with given ID not found
        """
        # Get task
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Clear schedule data
        task.daily_allocations = {}

        # Set deleted flag
        task.is_deleted = True

        # Save changes
        self.repository.save(task)

        return task
