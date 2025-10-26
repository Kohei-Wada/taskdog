"""Use case for setting task tags."""

from application.dto.set_task_tags_request import SetTaskTagsRequest
from application.use_cases.base import UseCase
from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository


class SetTaskTagsUseCase(UseCase[SetTaskTagsRequest, Task]):
    """Use case for setting task tags.

    Completely replaces the existing tags with the new tags.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: SetTaskTagsRequest) -> Task:
        """Execute tag setting.

        Args:
            input_dto: Tag setting input data

        Returns:
            Updated task

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskValidationError: If tags are invalid (empty strings or duplicates)
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Replace tags (validation happens in Task.__post_init__)
        task.tags = input_dto.tags

        # Save changes
        self.repository.save(task)

        return task
