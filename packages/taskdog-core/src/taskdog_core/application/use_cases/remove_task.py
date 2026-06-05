"""Use case for removing a task."""

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.task_repository import TaskRepository


class RemoveTaskUseCase(UseCase[SingleTaskInput, TaskOperationOutput]):
    """Use case for removing tasks."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: SingleTaskInput) -> TaskOperationOutput:
        """Execute task removal.

        Deletes both the task and its associated notes (if any). Notes are
        removed in the same transaction via the ``ON DELETE CASCADE`` foreign
        key. Returns task information captured before deletion.

        Args:
            input_dto: Task removal input data

        Returns:
            TaskOperationOutput containing the deleted task's information

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Capture task info before deletion
        result = TaskOperationOutput.from_task(task)

        # Delete the task and its associated notes atomically
        # (SqliteTaskRepository handles both in a single transaction)
        self.repository.delete(input_dto.task_id)

        return result
