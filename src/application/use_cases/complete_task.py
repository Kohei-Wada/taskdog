"""Use case for completing a task."""

from application.dto.complete_task_input import CompleteTaskInput
from application.use_cases.status_change_use_case import StatusChangeUseCase
from domain.entities.task import TaskStatus


class CompleteTaskUseCase(StatusChangeUseCase[CompleteTaskInput]):
    """Use case for completing a task.

    Sets task status to COMPLETED and records actual end time.

    This use case inherits common status change logic from StatusChangeUseCase
    and only specifies the target status.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return COMPLETED as the target status.

        Returns:
            TaskStatus.COMPLETED
        """
        return TaskStatus.COMPLETED
