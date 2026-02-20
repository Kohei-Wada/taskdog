"""Task relationship controller for managing task relationships and metadata.

This controller handles operations related to task relationships and metadata:
- add_dependency: Add dependency relationship between tasks (with cycle detection)
- remove_dependency: Remove dependency relationship
- set_task_tags: Replace all tags for a task
- delete_tag: Delete a tag from the system
"""

from taskdog_core.application.dto.delete_tag_input import DeleteTagInput
from taskdog_core.application.dto.delete_tag_output import DeleteTagOutput
from taskdog_core.application.dto.manage_dependencies_input import (
    AddDependencyInput,
    RemoveDependencyInput,
)
from taskdog_core.application.dto.set_task_tags_input import SetTaskTagsInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.add_dependency import AddDependencyUseCase
from taskdog_core.application.use_cases.delete_tag import DeleteTagUseCase
from taskdog_core.application.use_cases.remove_dependency import RemoveDependencyUseCase
from taskdog_core.application.use_cases.set_task_tags import SetTaskTagsUseCase
from taskdog_core.controllers.base_controller import BaseTaskController
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.logger import Logger
from taskdog_core.shared.config_manager import Config


class TaskRelationshipController(BaseTaskController):
    """Controller for task relationship and metadata operations.

    Handles operations related to task relationships and metadata:
    - Managing task dependencies (add/remove with cycle detection)
    - Managing task tags (replace all tags)

    All operations maintain data integrity and validate relationships.

    Attributes:
        repository: Task repository (inherited from BaseTaskController)
        config: Application configuration (inherited from BaseTaskController)
        logger: Optional logger (inherited from BaseTaskController)
    """

    def __init__(self, repository: TaskRepository, config: Config, logger: Logger):
        """Initialize the relationship controller.

        Args:
            repository: Task repository
            config: Application configuration
            logger: Logger for operation tracking
        """
        super().__init__(repository, config, logger)

    def add_dependency(self, task_id: int, depends_on_id: int) -> TaskOperationOutput:
        """Add a dependency to a task.

        Args:
            task_id: ID of the task to add dependency to
            depends_on_id: ID of the dependency task to add

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task or dependency not found
            TaskValidationError: If dependency would create a cycle, or task depends on itself
        """
        use_case = AddDependencyUseCase(self.repository)
        request = AddDependencyInput(task_id=task_id, depends_on_id=depends_on_id)
        return use_case.execute(request)

    def remove_dependency(
        self, task_id: int, depends_on_id: int
    ) -> TaskOperationOutput:
        """Remove a dependency from a task.

        Args:
            task_id: ID of the task to remove dependency from
            depends_on_id: ID of the dependency task to remove

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If dependency doesn't exist on task
        """
        use_case = RemoveDependencyUseCase(self.repository)
        request = RemoveDependencyInput(task_id=task_id, depends_on_id=depends_on_id)
        return use_case.execute(request)

    def set_task_tags(self, task_id: int, tags: list[str]) -> TaskOperationOutput:
        """Set task tags (completely replaces existing tags).

        Args:
            task_id: ID of the task to set tags for
            tags: List of tags to set

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If tags are invalid (empty strings or duplicates)
        """
        use_case = SetTaskTagsUseCase(self.repository)
        request = SetTaskTagsInput(task_id=task_id, tags=tags)
        return use_case.execute(request)

    def delete_tag(self, tag_name: str) -> DeleteTagOutput:
        """Delete a tag from the system.

        Removes the tag and all its associations with tasks.

        Args:
            tag_name: Name of the tag to delete

        Returns:
            DeleteTagOutput with tag name and affected task count

        Raises:
            TagNotFoundException: If tag not found
        """
        use_case = DeleteTagUseCase(self.repository)
        request = DeleteTagInput(tag_name=tag_name)
        return use_case.execute(request)
