"""Use case for restoring an archived task."""

from application.dto.restore_task_request import RestoreTaskRequest
from application.use_cases.base import UseCase
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from domain.repositories.task_repository import TaskRepository


class RestoreTaskUseCase(UseCase[RestoreTaskRequest, Task]):
    """Use case for restoring archived tasks.

    Restores an archived task back to its original status.
    This use case:
    - Clears is_archived flag (sets to False)
    - Preserves the task's original status (PENDING, COMPLETED, CANCELED, etc.)
    - Makes the task visible in active views again
    - Does not modify other fields (schedule, timestamps, etc.)

    This is primarily intended for recovering from accidental archiving.
    """

    def __init__(self, repository: TaskRepository) -> None:
        """Initialize use case with repository.

        Args:
            repository: Task repository for persistence
        """
        self.repository = repository

    def execute(self, input_dto: RestoreTaskRequest) -> Task:
        """Restore an archived task.

        Args:
            input_dto: Input containing task_id

        Returns:
            Restored task

        Raises:
            TaskNotFoundException: If task does not exist
            TaskValidationError: If task is not archived
        """
        # Get task
        task = self.repository.get_by_id(input_dto.task_id)
        if not task:
            raise TaskNotFoundException(input_dto.task_id)

        # Validate: can only restore archived tasks
        if not task.is_archived:
            raise TaskValidationError(
                f"Cannot restore task with ID {input_dto.task_id}. "
                "Only archived tasks can be restored."
            )

        # Clear archived flag
        task.is_archived = False

        # Save and return
        self.repository.save(task)
        return task
