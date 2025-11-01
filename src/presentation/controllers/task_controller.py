"""Task controller for orchestrating use cases.

This controller provides a shared interface between CLI and TUI layers,
eliminating code duplication in use case instantiation and DTO construction.
"""

from datetime import datetime

from application.dto.archive_task_request import ArchiveTaskRequest
from application.dto.cancel_task_request import CancelTaskRequest
from application.dto.complete_task_request import CompleteTaskRequest
from application.dto.create_task_request import CreateTaskRequest
from application.dto.manage_dependencies_request import RemoveDependencyRequest
from application.dto.pause_task_request import PauseTaskRequest
from application.dto.remove_task_request import RemoveTaskRequest
from application.dto.reopen_task_request import ReopenTaskRequest
from application.dto.restore_task_request import RestoreTaskRequest
from application.dto.set_task_tags_request import SetTaskTagsRequest
from application.dto.start_task_request import StartTaskRequest
from application.use_cases.archive_task import ArchiveTaskUseCase
from application.use_cases.cancel_task import CancelTaskUseCase
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.pause_task import PauseTaskUseCase
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from application.use_cases.reopen_task import ReopenTaskUseCase
from application.use_cases.restore_task import RestoreTaskUseCase
from application.use_cases.set_task_tags import SetTaskTagsUseCase
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import Task
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from shared.config_manager import Config


class TaskController:
    """Controller for task operations.

    This class orchestrates use cases, handling instantiation and DTO construction.
    Presentation layers (CLI/TUI) only need to call controller methods with
    simple parameters, without knowing about use cases or DTOs.

    Attributes:
        repository: Task repository for data persistence
        time_tracker: Time tracker for recording timestamps
        config: Application configuration
    """

    def __init__(
        self,
        repository: TaskRepository,
        time_tracker: TimeTracker,
        config: Config,
    ):
        """Initialize the task controller.

        Args:
            repository: Task repository
            time_tracker: Time tracker service
            config: Configuration
        """
        self.repository = repository
        self.time_tracker = time_tracker
        self.config = config

    def start_task(self, task_id: int) -> Task:
        """Start a task.

        Changes task status to IN_PROGRESS and records actual start time.

        Args:
            task_id: ID of the task to start

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be started
        """
        use_case = StartTaskUseCase(self.repository, self.time_tracker)
        request = StartTaskRequest(task_id=task_id)
        return use_case.execute(request)

    def complete_task(self, task_id: int) -> Task:
        """Complete a task.

        Changes task status to COMPLETED and records actual end time.

        Args:
            task_id: ID of the task to complete

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be completed
        """
        use_case = CompleteTaskUseCase(self.repository, self.time_tracker)
        request = CompleteTaskRequest(task_id=task_id)
        return use_case.execute(request)

    def pause_task(self, task_id: int) -> Task:
        """Pause a task.

        Changes task status to PENDING and clears actual start/end times.

        Args:
            task_id: ID of the task to pause

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be paused
        """
        use_case = PauseTaskUseCase(self.repository, self.time_tracker)
        request = PauseTaskRequest(task_id=task_id)
        return use_case.execute(request)

    def cancel_task(self, task_id: int) -> Task:
        """Cancel a task.

        Changes task status to CANCELED and records actual end time.

        Args:
            task_id: ID of the task to cancel

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be canceled
        """
        use_case = CancelTaskUseCase(self.repository, self.time_tracker)
        request = CancelTaskRequest(task_id=task_id)
        return use_case.execute(request)

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
    ) -> Task:
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
            The created task

        Raises:
            TaskValidationError: If task validation fails
        """
        use_case = CreateTaskUseCase(self.repository)
        request = CreateTaskRequest(
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

    def reopen_task(self, task_id: int) -> Task:
        """Reopen a task.

        Changes task status to PENDING and clears actual start/end times.

        Args:
            task_id: ID of the task to reopen

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be reopened
        """
        use_case = ReopenTaskUseCase(self.repository, self.time_tracker)
        request = ReopenTaskRequest(task_id=task_id)
        return use_case.execute(request)

    def archive_task(self, task_id: int) -> Task:
        """Archive a task (soft delete).

        Sets is_archived flag to True, preserving task data.

        Args:
            task_id: ID of the task to archive

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be archived
        """
        use_case = ArchiveTaskUseCase(self.repository)
        request = ArchiveTaskRequest(task_id=task_id)
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
        request = RemoveTaskRequest(task_id=task_id)
        use_case.execute(request)

    def restore_task(self, task_id: int) -> Task:
        """Restore an archived task.

        Sets is_archived flag to False, making the task visible again.

        Args:
            task_id: ID of the task to restore

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be restored
        """
        use_case = RestoreTaskUseCase(self.repository)
        request = RestoreTaskRequest(task_id=task_id)
        return use_case.execute(request)

    def remove_dependency(self, task_id: int, depends_on_id: int) -> Task:
        """Remove a dependency from a task.

        Args:
            task_id: ID of the task to remove dependency from
            depends_on_id: ID of the dependency task to remove

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If dependency doesn't exist on task
        """
        use_case = RemoveDependencyUseCase(self.repository)
        request = RemoveDependencyRequest(task_id=task_id, depends_on_id=depends_on_id)
        return use_case.execute(request)

    def set_task_tags(self, task_id: int, tags: list[str]) -> Task:
        """Set task tags (completely replaces existing tags).

        Args:
            task_id: ID of the task to set tags for
            tags: List of tags to set

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If tags are invalid (empty strings or duplicates)
        """
        use_case = SetTaskTagsUseCase(self.repository)
        request = SetTaskTagsRequest(task_id=task_id, tags=tags)
        return use_case.execute(request)
