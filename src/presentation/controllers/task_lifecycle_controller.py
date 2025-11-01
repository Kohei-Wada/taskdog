"""Task lifecycle controller for status change operations.

This controller handles all task lifecycle operations (status changes with time tracking):
- start_task: Change status to IN_PROGRESS, record start time
- complete_task: Change status to COMPLETED, record end time
- pause_task: Reset to PENDING, clear timestamps
- cancel_task: Change status to CANCELED, record end time
- reopen_task: Reset finished task to PENDING, clear timestamps
"""

from application.dto.cancel_task_input import CancelTaskInput
from application.dto.complete_task_input import CompleteTaskInput
from application.dto.pause_task_input import PauseTaskInput
from application.dto.reopen_task_input import ReopenTaskInput
from application.dto.start_task_input import StartTaskInput
from application.dto.task_operation_output import TaskOperationOutput
from application.use_cases.cancel_task import CancelTaskUseCase
from application.use_cases.complete_task import CompleteTaskUseCase
from application.use_cases.pause_task import PauseTaskUseCase
from application.use_cases.reopen_task import ReopenTaskUseCase
from application.use_cases.start_task import StartTaskUseCase
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from presentation.controllers.base_controller import BaseTaskController
from shared.config_manager import Config


class TaskLifecycleController(BaseTaskController):
    """Controller for task lifecycle operations.

    Handles all status change operations with time tracking:
    - Starting tasks (PENDING → IN_PROGRESS)
    - Completing tasks (IN_PROGRESS → COMPLETED)
    - Pausing tasks (IN_PROGRESS → PENDING)
    - Canceling tasks (any status → CANCELED)
    - Reopening tasks (COMPLETED/CANCELED → PENDING)

    All operations record appropriate timestamps via TimeTracker.

    Attributes:
        repository: Task repository (inherited from BaseTaskController)
        config: Application configuration (inherited from BaseTaskController)
        time_tracker: Time tracker for recording timestamps
    """

    def __init__(
        self,
        repository: TaskRepository,
        time_tracker: TimeTracker,
        config: Config,
    ):
        """Initialize the lifecycle controller.

        Args:
            repository: Task repository
            time_tracker: Time tracker service for recording timestamps
            config: Application configuration
        """
        super().__init__(repository, config)
        self.time_tracker = time_tracker

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
        use_case = StartTaskUseCase(self.repository, self.time_tracker)
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
        use_case = CompleteTaskUseCase(self.repository, self.time_tracker)
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
        use_case = PauseTaskUseCase(self.repository, self.time_tracker)
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
        use_case = CancelTaskUseCase(self.repository, self.time_tracker)
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
        use_case = ReopenTaskUseCase(self.repository, self.time_tracker)
        request = ReopenTaskInput(task_id=task_id)
        return use_case.execute(request)
