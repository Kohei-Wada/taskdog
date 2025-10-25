"""Use case for restoring an archived task."""

from application.dto.restore_task_request import RestoreTaskRequest
from application.use_cases.status_change_use_case import StatusChangeUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskValidationError


class RestoreTaskUseCase(StatusChangeUseCase[RestoreTaskRequest]):
    """Use case for restoring archived tasks.

    Restores an archived task back to PENDING status.
    This use case:
    - Transitions task from ARCHIVED to PENDING
    - Makes the task visible in active views again
    - Does not modify other fields (schedule, timestamps, etc.)

    This is primarily intended for recovering from accidental archiving.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return PENDING as the target status.

        Returns:
            TaskStatus.PENDING
        """
        return TaskStatus.PENDING

    def _should_validate(self) -> bool:
        """Enable custom validation in _before_status_change.

        Returns:
            False to skip standard validation
        """
        return False

    def _before_status_change(self, task: Task) -> None:
        """Validate task can be restored.

        Args:
            task: Task that will be restored

        Raises:
            TaskValidationError: If task cannot be restored
        """
        # Validate: can only restore ARCHIVED tasks
        if task.status != TaskStatus.ARCHIVED:
            raise TaskValidationError(
                f"Cannot restore task with status {task.status.value}. "
                "Only ARCHIVED tasks can be restored."
            )
