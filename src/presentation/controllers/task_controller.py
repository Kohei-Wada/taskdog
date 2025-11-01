"""Task controller for orchestrating use cases.

This controller provides a shared interface between CLI and TUI layers,
eliminating code duplication in use case instantiation and DTO construction.
"""

from datetime import datetime

from application.dto.cancel_task_request import CancelTaskRequest
from application.dto.complete_task_request import CompleteTaskRequest
from application.dto.create_task_request import CreateTaskRequest
from application.dto.pause_task_request import PauseTaskRequest
from application.dto.start_task_request import StartTaskRequest
from application.use_cases.cancel_task import CancelTaskUseCase
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.create_task import CreateTaskUseCase
from application.use_cases.pause_task import PauseTaskUseCase
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
