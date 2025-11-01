"""Use case for setting task tags."""

from application.dto.set_task_tags_input import SetTaskTagsInput
from application.dto.task_operation_output import TaskOperationOutput
from application.use_cases.base import UseCase
from domain.exceptions.task_exceptions import TaskValidationError
from domain.repositories.task_repository import TaskRepository


class SetTaskTagsUseCase(UseCase[SetTaskTagsInput, TaskOperationOutput]):
    """Use case for setting task tags.

    Completely replaces the existing tags with the new tags.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: SetTaskTagsInput) -> TaskOperationOutput:
        """Execute tag setting.

        Args:
            input_dto: Tag setting input data

        Returns:
            TaskOperationOutput DTO containing updated task information

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskValidationError: If tags are invalid (empty strings or duplicates)
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Validate tags before setting
        for tag in input_dto.tags:
            if not tag or not tag.strip():
                raise TaskValidationError("Tag cannot be empty")
        if len(input_dto.tags) != len(set(input_dto.tags)):
            raise TaskValidationError("Tags must be unique")

        # Replace tags
        task.tags = input_dto.tags

        # Save changes
        self.repository.save(task)

        return TaskOperationOutput.from_task(task)
