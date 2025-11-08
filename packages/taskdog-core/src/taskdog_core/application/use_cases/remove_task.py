"""Use case for removing a task."""

from taskdog_core.application.dto.remove_task_input import RemoveTaskInput
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.task_repository import TaskRepository


class RemoveTaskUseCase(UseCase[RemoveTaskInput, None]):
    """Use case for removing tasks."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: RemoveTaskInput) -> None:
        """Execute task removal.

        Args:
            input_dto: Task removal input data

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        self._get_task_or_raise(self.repository, input_dto.task_id)
        self.repository.delete(input_dto.task_id)
