"""Task controller for orchestrating use cases.

This controller provides a shared interface between CLI and TUI layers,
eliminating code duplication in use case instantiation and DTO construction.
"""

from application.dto.start_task_request import StartTaskRequest
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import Task
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from shared.config_manager import ConfigManager


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
        repository: JsonTaskRepository,
        time_tracker: TimeTracker,
        config: ConfigManager,
    ):
        """Initialize the task controller.

        Args:
            repository: Task repository
            time_tracker: Time tracker service
            config: Configuration manager
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
