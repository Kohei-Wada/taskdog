"""Use case for canceling a task."""

from application.dto.cancel_task_input import CancelTaskInput
from application.use_cases.status_change_use_case import StatusChangeUseCase
from domain.entities.task import TaskStatus


class CancelTaskUseCase(StatusChangeUseCase[CancelTaskInput]):
    """Use case for canceling a task.

    Sets task status to CANCELED and records actual end time.

    This use case inherits common status change logic from StatusChangeUseCase
    and only specifies the target status.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return CANCELED as the target status.

        Returns:
            TaskStatus.CANCELED
        """
        return TaskStatus.CANCELED
