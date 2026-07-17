"""Task lifecycle controller for status change operations.

This controller handles all task lifecycle operations (status changes with time tracking):
- start_task: Change status to IN_PROGRESS, record start time
- complete_task: Change status to COMPLETED, record end time
- pause_task: Reset to PENDING, clear timestamps
- cancel_task: Change status to CANCELED, record end time
- reopen_task: Reset finished task to PENDING, clear timestamps
"""

from datetime import datetime
from types import EllipsisType

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.dto.fix_actual_times_input import FixActualTimesInput
from taskdog_core.application.dto.status_change_output import StatusChangeOutput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.fix_actual_times import FixActualTimesUseCase
from taskdog_core.application.use_cases.lifecycle_registry import LIFECYCLE_USE_CASES
from taskdog_core.controllers.base_controller import BaseTaskController


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
    """

    def execute_lifecycle(self, operation: str, task_id: int) -> StatusChangeOutput:
        """Execute a lifecycle status change on a task.

        Args:
            operation: One of start, complete, pause, cancel, reopen.
            task_id: ID of the task to modify.

        Returns:
            StatusChangeOutput containing the updated task and old status.

        Raises:
            ValueError: If operation is not a valid lifecycle operation.
            TaskNotFoundException: If task not found.
            TaskValidationError: If the transition is not allowed.
        """
        use_case_cls = LIFECYCLE_USE_CASES.get(operation)
        if use_case_cls is None:
            raise ValueError(f"Invalid lifecycle operation: {operation}")
        use_case = use_case_cls(self.repository)
        return use_case.execute(SingleTaskInput(task_id=task_id))

    def fix_actual_times(
        self,
        task_id: int,
        actual_start: datetime | None | EllipsisType = ...,
        actual_end: datetime | None | EllipsisType = ...,
        actual_duration: float | None | EllipsisType = ...,
    ) -> TaskOperationOutput:
        """Fix actual start/end timestamps and/or duration for a task.

        Used to correct timestamps after the fact, for historical accuracy.
        Past dates are allowed since these are historical records.

        Args:
            task_id: ID of the task to fix
            actual_start: New actual start (None to clear, ... to keep current)
            actual_end: New actual end (None to clear, ... to keep current)
            actual_duration: Explicit duration in hours (None to clear, ... to keep current)

        Returns:
            TaskOperationOutput containing the updated task information

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If actual_end < actual_start when both are set
            TaskValidationError: If actual_duration is set but <= 0
        """
        use_case = FixActualTimesUseCase(self.repository)
        request = FixActualTimesInput(
            task_id=task_id,
            actual_start=actual_start,
            actual_end=actual_end,
            actual_duration=actual_duration,
        )
        return use_case.execute(request)
