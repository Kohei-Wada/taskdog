"""Task controller for orchestrating use cases.

This controller provides a shared interface between CLI and TUI layers,
eliminating code duplication in use case instantiation and DTO construction.
"""

from datetime import datetime

from application.dto.archive_task_request import ArchiveTaskRequest
from application.dto.cancel_task_request import CancelTaskRequest
from application.dto.complete_task_request import CompleteTaskRequest
from application.dto.create_task_request import CreateTaskRequest
from application.dto.log_hours_request import LogHoursRequest
from application.dto.manage_dependencies_request import (
    AddDependencyRequest,
    RemoveDependencyRequest,
)
from application.dto.pause_task_request import PauseTaskRequest
from application.dto.remove_task_request import RemoveTaskRequest
from application.dto.reopen_task_request import ReopenTaskRequest
from application.dto.restore_task_request import RestoreTaskRequest
from application.dto.set_task_tags_request import SetTaskTagsRequest
from application.dto.start_task_request import StartTaskRequest
from application.dto.statistics_result import CalculateStatisticsRequest, StatisticsResult
from application.dto.task_detail_result import GetTaskDetailResult
from application.dto.update_task_request import UpdateTaskRequest
from application.use_cases.add_dependency import AddDependencyUseCase
from application.use_cases.archive_task import ArchiveTaskUseCase
from application.use_cases.calculate_statistics import CalculateStatisticsUseCase
from application.use_cases.cancel_task import CancelTaskUseCase
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.get_task_detail import GetTaskDetailInput, GetTaskDetailUseCase
from application.use_cases.log_hours import LogHoursUseCase
from application.use_cases.pause_task import PauseTaskUseCase
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from application.use_cases.remove_task import RemoveTaskUseCase
from application.use_cases.reopen_task import ReopenTaskUseCase
from application.use_cases.restore_task import RestoreTaskUseCase
from application.use_cases.set_task_tags import SetTaskTagsUseCase
from application.use_cases.start_task import StartTaskUseCase
from application.use_cases.update_task import UpdateTaskUseCase
from domain.entities.task import Task, TaskStatus
from domain.repositories.notes_repository import NotesRepository
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
        notes_repository: Notes repository for notes file operations (optional)
    """

    def __init__(
        self,
        repository: TaskRepository,
        time_tracker: TimeTracker,
        config: Config,
        notes_repository: NotesRepository | None = None,
    ):
        """Initialize the task controller.

        Args:
            repository: Task repository
            time_tracker: Time tracker service
            config: Configuration
            notes_repository: Notes repository (optional, required for get_task_detail)
        """
        self.repository = repository
        self.time_tracker = time_tracker
        self.config = config
        self.notes_repository = notes_repository

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

    def add_dependency(self, task_id: int, depends_on_id: int) -> Task:
        """Add a dependency to a task.

        Args:
            task_id: ID of the task to add dependency to
            depends_on_id: ID of the dependency task to add

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task or dependency not found
            TaskValidationError: If dependency would create a cycle, or task depends on itself
        """
        use_case = AddDependencyUseCase(self.repository)
        request = AddDependencyRequest(task_id=task_id, depends_on_id=depends_on_id)
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

    def log_hours(self, task_id: int, hours: float, date: str) -> Task:
        """Log actual hours worked on a task for a specific date.

        Args:
            task_id: ID of the task to log hours for
            hours: Number of hours worked (must be > 0)
            date: Date in YYYY-MM-DD format

        Returns:
            The updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If date format is invalid or hours <= 0
        """
        use_case = LogHoursUseCase(self.repository)
        request = LogHoursRequest(task_id=task_id, hours=hours, date=date)
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
    ) -> tuple[Task, list[str]]:
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
            Tuple of (updated task, list of updated field names)

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If validation fails for any field
        """
        use_case = UpdateTaskUseCase(self.repository, self.time_tracker)
        request = UpdateTaskRequest(
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

    def get_task_detail(self, task_id: int) -> GetTaskDetailResult:
        """Get task details with notes.

        Args:
            task_id: ID of the task to retrieve

        Returns:
            GetTaskDetailResult containing task and notes information

        Raises:
            TaskNotFoundException: If task not found
            ValueError: If notes_repository is not initialized
        """
        if self.notes_repository is None:
            raise ValueError("notes_repository is required for get_task_detail operation")

        use_case = GetTaskDetailUseCase(self.repository, self.notes_repository)
        input_dto = GetTaskDetailInput(task_id)
        return use_case.execute(input_dto)

    def calculate_statistics(self, period: str = "all") -> StatisticsResult:
        """Calculate task statistics.

        Args:
            period: Time period for filtering ('7d', '30d', or 'all')

        Returns:
            StatisticsResult containing comprehensive task statistics

        Raises:
            ValueError: If period is invalid
        """
        if period not in ["all", "7d", "30d"]:
            raise ValueError(f"Invalid period: {period}. Must be 'all', '7d', or '30d'")

        use_case = CalculateStatisticsUseCase(self.repository)
        request = CalculateStatisticsRequest(period=period)
        return use_case.execute(request)
