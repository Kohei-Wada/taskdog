"""Use case for reopening a completed or canceled task."""

from application.dto.reopen_task_request import ReopenTaskRequest
from application.use_cases.status_change_use_case import StatusChangeUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskValidationError


class ReopenTaskUseCase(StatusChangeUseCase[ReopenTaskRequest]):
    """Use case for reopening a completed or canceled task.

    Reopening transitions a task from COMPLETED or CANCELED back to PENDING.

    Note: Dependencies are NOT validated during reopen. This allows flexible
    restoration of task states. Dependency validation will occur when the task
    is started again via StartTaskUseCase.

    This use case inherits common status change logic from StatusChangeUseCase
    and uses the _before_status_change hook to validate reopening and clear
    time tracking data.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return PENDING as the target status.

        Returns:
            TaskStatus.PENDING
        """
        return TaskStatus.PENDING

    def _should_validate(self) -> bool:
        """Skip standard status validation.

        We use custom validation in _before_status_change instead, because
        reopening has unique validation requirements (only from COMPLETED
        or CANCELED, and must not be deleted).

        Returns:
            False to skip standard validation
        """
        return False

    def _before_status_change(self, task: Task) -> None:
        """Validate task can be reopened and clear time tracking.

        Args:
            task: Task that will be reopened

        Raises:
            TaskValidationError: If task cannot be reopened
        """
        # Validate: can only reopen COMPLETED or CANCELED tasks
        if task.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELED):
            raise TaskValidationError(
                f"Cannot reopen task with status {task.status.value}. "
                "Only COMPLETED or CANCELED tasks can be reopened."
            )

        # Validate: cannot reopen deleted tasks
        if task.is_deleted:
            raise TaskValidationError(
                "Cannot reopen deleted task. Restore the task first with 'restore' command."
            )

        # Clear time tracking (reset timestamps)
        self.time_tracker.clear_time_tracking(task)
