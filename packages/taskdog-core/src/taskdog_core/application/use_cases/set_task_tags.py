"""Use case for setting task tags."""

from dataclasses import replace

from taskdog_core.application.dto.set_task_tags_input import SetTaskTagsInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.task_repository import TaskRepository


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
            TaskValidationError: If tags violate the Task entity's tag invariants
                (empty strings, duplicates, too many tags, or a tag that is too long)
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Rebuild task to trigger __post_init__ validation (Always-Valid Entity).
        # Direct attribute assignment would skip Task._validate_tags, which also
        # enforces the maximum tag count and tag length.
        task = replace(task, tags=input_dto.tags)

        # Save changes
        self.repository.save(task)

        return TaskOperationOutput.from_task(task)
