"""Task lifecycle controller for status change operations.

This controller handles all task lifecycle operations (status changes with time tracking):
- start_task: Change status to IN_PROGRESS, record start time
- complete_task: Change status to COMPLETED, record end time
- pause_task: Reset to PENDING, clear timestamps
- cancel_task: Change status to CANCELED, record end time
- reopen_task: Reset finished task to PENDING, clear timestamps
"""

from taskdog_core.application.dto.cancel_task_input import CancelTaskInput
from taskdog_core.application.dto.complete_task_input import CompleteTaskInput
from taskdog_core.application.dto.pause_task_input import PauseTaskInput
from taskdog_core.application.dto.reopen_task_input import ReopenTaskInput
from taskdog_core.application.dto.start_task_input import StartTaskInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.cancel_task import CancelTaskUseCase
from taskdog_core.application.use_cases.complete_task import CompleteTaskUseCase
from taskdog_core.application.use_cases.pause_task import PauseTaskUseCase
from taskdog_core.application.use_cases.reopen_task import ReopenTaskUseCase
from taskdog_core.application.use_cases.start_task import StartTaskUseCase
from taskdog_core.controllers.base_controller import BaseTaskController
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.logger import Logger
from taskdog_core.shared.server_config_manager import ServerConfig


class TaskLifecycleController(BaseTaskController):
    """Controller for task lifecycle operations.

    Handles all status change operations with time tracking:
    - Starting tasks (PENDING → IN_PROGRESS)
    - Completing tasks (IN_PROGRESS → COMPLETED)
    - Pausing tasks (IN_PROGRESS → PENDING)
    - Canceling tasks (any status → CANCELED)
    - Reopening tasks (COMPLETED/CANCELED → PENDING)

    All operations record appropriate timestamps via Task entity methods.

    Attributes:
        repository: Task repository (inherited from BaseTaskController)
        config: Application configuration (inherited from BaseTaskController)
        logger: Optional logger (inherited from BaseTaskController)
    """

    def __init__(
        self,
        repository: TaskRepository,
        config: ServerConfig,
        logger: Logger | None = None,
    ):
        """Initialize the lifecycle controller.

        Args:
            repository: Task repository
            config: Application configuration
            logger: Optional logger for operation tracking
        """
        super().__init__(repository, config, logger)

    def start_task(self, task_id: int) -> TaskOperationOutput:
        """Start a task.

        Changes task status to IN_PROGRESS and records actual start time.

        Args:
            task_id: ID of the task to start

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be started
        """
        use_case = StartTaskUseCase(self.repository)
        request = StartTaskInput(task_id=task_id)
        return use_case.execute(request)

    def complete_task(self, task_id: int) -> TaskOperationOutput:
        """Complete a task.

        Changes task status to COMPLETED and records actual end time.

        Args:
            task_id: ID of the task to complete

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be completed
        """
        use_case = CompleteTaskUseCase(self.repository)
        request = CompleteTaskInput(task_id=task_id)
        return use_case.execute(request)

    def pause_task(self, task_id: int) -> TaskOperationOutput:
        """Pause a task.

        Changes task status to PENDING and clears actual start/end times.

        Args:
            task_id: ID of the task to pause

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be paused
        """
        use_case = PauseTaskUseCase(self.repository)
        request = PauseTaskInput(task_id=task_id)
        return use_case.execute(request)

    def cancel_task(self, task_id: int) -> TaskOperationOutput:
        """Cancel a task.

        Changes task status to CANCELED and records actual end time.

        Args:
            task_id: ID of the task to cancel

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be canceled
        """
        use_case = CancelTaskUseCase(self.repository)
        request = CancelTaskInput(task_id=task_id)
        return use_case.execute(request)

    def reopen_task(self, task_id: int) -> TaskOperationOutput:
        """Reopen a task.

        Changes task status to PENDING and clears actual start/end times.

        Args:
            task_id: ID of the task to reopen

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If task cannot be reopened
        """
        use_case = ReopenTaskUseCase(self.repository)
        request = ReopenTaskInput(task_id=task_id)
        return use_case.execute(request)
