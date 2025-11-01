"""Task relationship controller for managing task relationships and metadata.

This controller handles operations related to task relationships and metadata:
- add_dependency: Add dependency relationship between tasks (with cycle detection)
- remove_dependency: Remove dependency relationship
- set_task_tags: Replace all tags for a task
- log_hours: Log actual hours worked on a specific date
"""

from application.dto.log_hours_input import LogHoursInput
from application.dto.manage_dependencies_input import (
    AddDependencyInput,
    RemoveDependencyInput,
)
from application.dto.set_task_tags_input import SetTaskTagsInput
from application.dto.task_operation_output import TaskOperationOutput
from application.use_cases.add_dependency import AddDependencyUseCase
from application.use_cases.log_hours import LogHoursUseCase
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from application.use_cases.set_task_tags import SetTaskTagsUseCase
from domain.repositories.task_repository import TaskRepository
from presentation.controllers.base_controller import BaseTaskController
from shared.config_manager import Config


class TaskRelationshipController(BaseTaskController):
    """Controller for task relationship and metadata operations.

    Handles operations related to task relationships and metadata:
    - Managing task dependencies (add/remove with cycle detection)
    - Managing task tags (replace all tags)
    - Logging actual hours worked

    All operations maintain data integrity and validate relationships.

    Attributes:
        repository: Task repository (inherited from BaseTaskController)
        config: Application configuration (inherited from BaseTaskController)
    """

    def __init__(self, repository: TaskRepository, config: Config):
        """Initialize the relationship controller.

        Args:
            repository: Task repository
            config: Application configuration
        """
        super().__init__(repository, config)

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

    def remove_dependency(self, task_id: int, depends_on_id: int) -> TaskOperationOutput:
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

    def log_hours(self, task_id: int, hours: float, date: str) -> TaskOperationOutput:
        """Log actual hours worked on a task for a specific date.

        Args:
            task_id: ID of the task to log hours for
            hours: Number of hours worked (must be > 0)
            date: Date in YYYY-MM-DD format

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If date format is invalid or hours <= 0
        """
        use_case = LogHoursUseCase(self.repository)
        request = LogHoursInput(task_id=task_id, hours=hours, date=date)
        return use_case.execute(request)
