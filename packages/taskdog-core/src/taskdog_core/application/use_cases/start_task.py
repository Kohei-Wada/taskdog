"""Use case for starting a task."""

from taskdog_core.application.dto.start_task_input import StartTaskInput
from taskdog_core.application.use_cases.status_change_use_case import (
    StatusChangeUseCase,
)
from taskdog_core.domain.entities.task import TaskStatus


class StartTaskUseCase(StatusChangeUseCase[StartTaskInput]):
    """Use case for starting a task.

    Sets task status to IN_PROGRESS and records actual start time.

    This use case inherits common status change logic from StatusChangeUseCase
    and only specifies the target status.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return IN_PROGRESS as the target status.

        Returns:
            TaskStatus.IN_PROGRESS
        """
        return TaskStatus.IN_PROGRESS
