"""Use case for archiving a task."""

from application.dto.archive_task_input import ArchiveTaskInput
from application.dto.task_operation_output import TaskOperationOutput
from application.use_cases.base import UseCase
from domain.repositories.task_repository import TaskRepository


class ArchiveTaskUseCase(UseCase[ArchiveTaskInput, TaskOperationOutput]):
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

    def execute(self, input_dto: ArchiveTaskInput) -> TaskOperationOutput:
        """Archive a task.

        Args:
            input_dto: Input containing task_id

        Returns:
            TaskOperationOutput DTO containing archived task information

        Raises:
            TaskNotFoundException: If task does not exist
        """
        # Get task
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Set archived flag
        task.is_archived = True

        # Clear schedule data
        task.daily_allocations = {}

        # Save and return
        self.repository.save(task)
        return TaskOperationOutput.from_task(task)
