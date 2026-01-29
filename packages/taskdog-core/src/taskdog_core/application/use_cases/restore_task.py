"""Use case for restoring an archived task."""

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError
from taskdog_core.domain.repositories.task_repository import TaskRepository


class RestoreTaskUseCase(UseCase[SingleTaskInput, TaskOperationOutput]):
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

    def execute(self, input_dto: SingleTaskInput) -> TaskOperationOutput:
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
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

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
        return TaskOperationOutput.from_task(task)
