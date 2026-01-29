"""Use case for pausing a task."""

from taskdog_core.application.dto.base import SingleTaskInput
from taskdog_core.application.use_cases.status_change_use_case import (
    StatusChangeUseCase,
)
from taskdog_core.domain.entities.task import TaskStatus


class PauseTaskUseCase(StatusChangeUseCase[SingleTaskInput]):
    """Use case for pausing a task.

    Sets task status to PENDING and clears actual start/end timestamps.
    This allows resetting a task that was started by mistake.

    This use case inherits common status change logic from StatusChangeUseCase.
    Time tracking (clearing actual_start/end timestamps) is handled automatically
    by Task.pause() method in TaskStatusService, so no pre-hook is needed.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return PENDING as the target status.

        Returns:
            TaskStatus.PENDING
        """
        return TaskStatus.PENDING
