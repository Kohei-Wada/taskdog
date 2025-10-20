"""Use case for restoring (undeleting) a task."""

from application.dto.restore_task_request import RestoreTaskRequest
from application.use_cases.base import UseCase
from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository


class RestoreTaskUseCase(UseCase[RestoreTaskRequest, Task]):
    """Use case for restoring archived (soft deleted) tasks.

    This use case:
    - Sets is_deleted flag to False
    - Makes the task visible in active views again
    - Does not modify task status or other fields
    """

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def execute(self, input_dto: RestoreTaskRequest) -> Task:
        """Restore (undelete) a task.

        Args:
            input_dto: RestoreTaskRequest containing task_id

        Returns:
            The restored task

        Raises:
            TaskNotFoundException: If task with given ID not found
        """
        # Get task (including deleted ones)
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Clear deleted flag
        task.is_deleted = False

        # Save changes
        self.repository.save(task)

        return task
