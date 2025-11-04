"""Task CRUD controller for basic create/read/update/delete operations.

This controller handles standard CRUD operations:
- create_task: Create a new task with all optional parameters
- update_task: Update multiple task fields at once
- archive_task: Soft delete (set is_archived=True)
- restore_task: Restore soft-deleted task (set is_archived=False)
- remove_task: Hard delete (permanent removal)
"""

from datetime import datetime

from application.dto.archive_task_input import ArchiveTaskInput
from application.dto.create_task_input import CreateTaskInput
from application.dto.remove_task_input import RemoveTaskInput
from application.dto.restore_task_input import RestoreTaskInput
from application.dto.task_operation_output import TaskOperationOutput
from application.dto.update_task_input import UpdateTaskInput
from application.dto.update_task_output import UpdateTaskOutput
from application.use_cases.archive_task import ArchiveTaskUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from application.use_cases.restore_task import RestoreTaskUseCase
from application.use_cases.update_task import UpdateTaskUseCase
from domain.entities.task import TaskStatus
from domain.repositories.task_repository import TaskRepository
from presentation.controllers.base_controller import BaseTaskController
from shared.config_manager import Config


class TaskCrudController(BaseTaskController):
    """Controller for task CRUD operations.

    Handles basic create, read, update, delete operations:
    - Creating new tasks with optional parameters
    - Updating multiple task fields
    - Archiving tasks (soft delete)
    - Restoring archived tasks
    - Removing tasks permanently (hard delete)

    The update operation supports time tracking via Task entity methods.

    Attributes:
        repository: Task repository (inherited from BaseTaskController)
        config: Application configuration (inherited from BaseTaskController)
    """

    def __init__(
        self,
        repository: TaskRepository,
        config: Config,
    ):
        """Initialize the CRUD controller.

        Args:
            repository: Task repository
            config: Application configuration
        """
        super().__init__(repository, config)

    def create_task(
        self,
        name: str,
        priority: int | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        is_fixed: bool = False,
        tags: list[str] | None = None,
    ) -> TaskOperationOutput:
        """Create a new task.

        Args:
            name: Task name
            priority: Task priority (default: from config)
            deadline: Task deadline (optional)
            estimated_duration: Estimated duration in hours (optional)
            planned_start: Planned start datetime (optional)
            planned_end: Planned end datetime (optional)
            is_fixed: Whether the task schedule is fixed (default: False)
            tags: List of tags for categorization (optional)

        Returns:
            TaskOperationOutput containing the created task information

        Raises:
            TaskValidationError: If task validation fails
        """
        use_case = CreateTaskUseCase(self.repository)
        request = CreateTaskInput(
            name=name,
            priority=priority or self.config.task.default_priority,
            deadline=deadline,
            estimated_duration=estimated_duration,
            planned_start=planned_start,
            planned_end=planned_end,
            is_fixed=is_fixed,
            tags=tags,
        )
        return use_case.execute(request)

    def update_task(
        self,
        task_id: int,
        name: str | None = None,
        priority: int | None = None,
        status: TaskStatus | None = None,
        planned_start: datetime | None = None,
        planned_end: datetime | None = None,
        deadline: datetime | None = None,
        estimated_duration: float | None = None,
        is_fixed: bool | None = None,
        tags: list[str] | None = None,
    ) -> UpdateTaskOutput:
        """Update task fields.

        Args:
            task_id: ID of the task to update
            name: New task name (optional)
            priority: New priority (optional)
            status: New status (optional)
            planned_start: New planned start datetime (optional)
            planned_end: New planned end datetime (optional)
            deadline: New deadline (optional)
            estimated_duration: New estimated duration in hours (optional)
            is_fixed: Whether task schedule is fixed (optional)
            tags: New tags list (optional)

        Returns:
            UpdateTaskOutput containing updated task info and list of updated field names

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails for any field
        """
        use_case = UpdateTaskUseCase(self.repository)
        request = UpdateTaskInput(
            task_id=task_id,
            name=name,
            priority=priority,
            status=status,
            planned_start=planned_start,
            planned_end=planned_end,
            deadline=deadline,
            estimated_duration=estimated_duration,
            is_fixed=is_fixed,
            tags=tags,
        )
        return use_case.execute(request)

    def archive_task(self, task_id: int) -> TaskOperationOutput:
        """Archive a task (soft delete).

        Sets is_archived flag to True, preserving task data.

        Args:
            task_id: ID of the task to archive

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be archived
        """
        use_case = ArchiveTaskUseCase(self.repository)
        request = ArchiveTaskInput(task_id=task_id)
        return use_case.execute(request)

    def restore_task(self, task_id: int) -> TaskOperationOutput:
        """Restore an archived task.

        Sets is_archived flag to False, making the task visible again.

        Args:
            task_id: ID of the task to restore

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be restored
        """
        use_case = RestoreTaskUseCase(self.repository)
        request = RestoreTaskInput(task_id=task_id)
        return use_case.execute(request)

    def remove_task(self, task_id: int) -> None:
        """Remove a task (hard delete).

        Permanently deletes the task from the repository.

        Args:
            task_id: ID of the task to remove

        Raises:
            TaskNotFoundException: If task not found
        """
        use_case = RemoveTaskUseCase(self.repository)
        request = RemoveTaskInput(task_id=task_id)
        use_case.execute(request)
