"""Task lifecycle controller for status change operations.

This controller handles all task lifecycle operations (status changes with time tracking):
- start_task: Change status to IN_PROGRESS, record start time
- complete_task: Change status to COMPLETED, record end time
- pause_task: Reset to PENDING, clear timestamps
- cancel_task: Change status to CANCELED, record end time
- reopen_task: Reset finished task to PENDING, clear timestamps
"""

from collections.abc import Callable
from datetime import datetime
from types import EllipsisType

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.fix_actual_times_input import FixActualTimesInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.cancel_task import CancelTaskUseCase
from taskdog_core.application.use_cases.complete_task import CompleteTaskUseCase
from taskdog_core.application.use_cases.fix_actual_times import FixActualTimesUseCase
from taskdog_core.application.use_cases.pause_task import PauseTaskUseCase
from taskdog_core.application.use_cases.reopen_task import ReopenTaskUseCase
from taskdog_core.application.use_cases.start_task import StartTaskUseCase
from taskdog_core.application.use_cases.status_change_use_case import (
    StatusChangeUseCase,
)
from taskdog_core.controllers.base_controller import BaseTaskController
from taskdog_core.domain.repositories.task_repository import TaskRepository
from taskdog_core.domain.services.logger import Logger
from taskdog_core.shared.config_manager import Config

# Type alias for use case factory function
StatusChangeUseCaseFactory = Callable[
    [TaskRepository], StatusChangeUseCase[SingleTaskInput]
]


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
        config: Config,
        logger: Logger,
    ):
        """Initialize the lifecycle controller.

        Args:
            repository: Task repository
            config: Application configuration
            logger: Logger for operation tracking
        """
        super().__init__(repository, config, logger)

    def _execute_status_change(
        self,
        use_case_factory: StatusChangeUseCaseFactory,
        task_id: int,
    ) -> TaskOperationOutput:
        """Execute a status change use case.

        Args:
            use_case_factory: Factory function (use case class) to instantiate
            task_id: ID of the task to modify

        Returns:
            TaskOperationOutput containing the updated task information
        """
        use_case = use_case_factory(self.repository)
        return use_case.execute(SingleTaskInput(task_id=task_id))

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
        return self._execute_status_change(StartTaskUseCase, task_id)

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
        return self._execute_status_change(CompleteTaskUseCase, task_id)

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
        return self._execute_status_change(PauseTaskUseCase, task_id)

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
        return self._execute_status_change(CancelTaskUseCase, task_id)

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
        return self._execute_status_change(ReopenTaskUseCase, task_id)

    def fix_actual_times(
        self,
        task_id: int,
        actual_start: datetime | None | EllipsisType = ...,
        actual_end: datetime | None | EllipsisType = ...,
    ) -> TaskOperationOutput:
        """Fix actual start/end timestamps for a task.

        Used to correct timestamps after the fact, for historical accuracy.
        Past dates are allowed since these are historical records.

        Args:
            task_id: ID of the task to fix
            actual_start: New actual start (None to clear, ... to keep current)
            actual_end: New actual end (None to clear, ... to keep current)

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If actual_end < actual_start when both are set
        """
        use_case = FixActualTimesUseCase(self.repository)
        request = FixActualTimesInput(
            task_id=task_id,
            actual_start=actual_start,
            actual_end=actual_end,
        )
        return use_case.execute(request)
