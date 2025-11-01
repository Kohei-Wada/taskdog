"""Use case for removing a task."""

from application.dto.remove_task_request import RemoveTaskRequest
from application.use_cases.base import UseCase
from domain.repositories.task_repository import TaskRepository


class RemoveTaskUseCase(UseCase[RemoveTaskRequest, None]):
    """Use case for removing tasks."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: RemoveTaskRequest) -> None:
        """Execute task removal.

        Args:
            input_dto: Task removal input data

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        self._get_task_or_raise(self.repository, input_dto.task_id)
        self.repository.delete(input_dto.task_id)
