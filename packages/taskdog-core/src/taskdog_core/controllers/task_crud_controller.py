"""Task CRUD controller for basic create/read/update/delete operations.

This controller handles standard CRUD operations:
- create_task: Create a new task with all optional parameters
- update_task: Update multiple task fields at once
- archive_task: Soft delete (set is_archived=True)
- restore_task: Restore soft-deleted task (set is_archived=False)
- remove_task: Hard delete (permanent removal)
"""

from datetime import datetime

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.dto.single_task_inputs import (
    ArchiveTaskInput,
    RemoveTaskInput,
    RestoreTaskInput,
)
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.dto.update_task_input import UpdateTaskInput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.application.use_cases.archive_task import ArchiveTaskUseCase
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.application.use_cases.remove_task import RemoveTaskUseCase
from taskdog_core.application.use_cases.restore_task import RestoreTaskUseCase
from taskdog_core.application.use_cases.update_task import UpdateTaskUseCase
from taskdog_core.controllers.base_controller import BaseTaskController
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.repositories.notes_repository import NotesRepository
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.logger import Logger
from taskdog_core.shared.config_manager import Config


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
        notes_repository: Notes repository for managing task notes
    """

    def __init__(
        self,
        repository: TaskRepository,
        notes_repository: NotesRepository,
        config: Config,
        logger: Logger,
    ):
        """Initialize the CRUD controller.

        Args:
            repository: Task repository
            notes_repository: Notes repository
            config: Application configuration
            logger: Logger for operation tracking
        """
        super().__init__(repository, config, logger)
        self.notes_repository = notes_repository

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
        self.logger.info(f"Creating task: name='{name}'", priority=priority)

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
        result = use_case.execute(request)

        self.logger.info(
            f"Task created successfully: id={result.id}", task_id=result.id
        )

        return result

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
    ) -> TaskUpdateOutput:
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
            TaskUpdateOutput containing updated task info and list of updated field names

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails for any field
        """
        self.logger.info(f"Updating task: task_id={task_id}", task_id=task_id)

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
        result = use_case.execute(request)

        self.logger.info(
            f"Task updated successfully: task_id={task_id}, fields={result.updated_fields}",
            task_id=task_id,
            updated_fields=result.updated_fields,
        )

        return result

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
        self.logger.info(f"Archiving task: task_id={task_id}", task_id=task_id)

        use_case = ArchiveTaskUseCase(self.repository)
        request = ArchiveTaskInput(task_id=task_id)
        result = use_case.execute(request)

        self.logger.info(
            f"Task archived successfully: task_id={task_id}", task_id=task_id
        )

        return result

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
        self.logger.info(f"Restoring task: task_id={task_id}", task_id=task_id)

        use_case = RestoreTaskUseCase(self.repository)
        request = RestoreTaskInput(task_id=task_id)
        result = use_case.execute(request)

        self.logger.info(
            f"Task restored successfully: task_id={task_id}", task_id=task_id
        )

        return result

    def remove_task(self, task_id: int) -> None:
        """Remove a task (hard delete).

        Permanently deletes the task and its associated notes from storage.

        Args:
            task_id: ID of the task to remove

        Raises:
            TaskNotFoundException: If task not found
        """
        self.logger.info(
            f"Removing task permanently: task_id={task_id}", task_id=task_id
        )

        use_case = RemoveTaskUseCase(self.repository, self.notes_repository)
        request = RemoveTaskInput(task_id=task_id)
        use_case.execute(request)

        self.logger.info(
            f"Task removed successfully: task_id={task_id}", task_id=task_id
        )
