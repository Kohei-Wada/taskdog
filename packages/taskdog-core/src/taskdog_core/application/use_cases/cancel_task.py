"""Use case for canceling a task."""

from taskdog_core.application.dto.cancel_task_input import CancelTaskInput
from taskdog_core.application.use_cases.status_change_use_case import (
    StatusChangeUseCase,
)
from taskdog_core.domain.entities.task import TaskStatus


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
