"""Use case for deleting a tag."""

from taskdog_core.application.dto.delete_tag_input import DeleteTagInput
from taskdog_core.application.dto.delete_tag_output import DeleteTagOutput
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.task_repository import TaskRepository


class DeleteTagUseCase(UseCase[DeleteTagInput, DeleteTagOutput]):
    """Use case for deleting a tag from the system.

    Deletes the tag record from the tags table. CASCADE delete
    automatically removes all task_tags associations.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize use case.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: DeleteTagInput) -> DeleteTagOutput:
        """Execute tag deletion.

        Args:
            input_dto: Tag deletion input data

        Returns:
            DeleteTagOutput with tag name and affected task count

        Raises:
            TagNotFoundException: If tag doesn't exist
        """
        affected_task_count = self.repository.delete_tag(input_dto.tag_name)

        return DeleteTagOutput(
            tag_name=input_dto.tag_name,
            affected_task_count=affected_task_count,
        )
