"""Use case for pausing a task."""

from application.dto.pause_task_input import PauseTaskInput
from application.use_cases.status_change_use_case import StatusChangeUseCase
from domain.entities.task import Task, TaskStatus


class PauseTaskUseCase(StatusChangeUseCase[PauseTaskInput]):
    """Use case for pausing a task.

    Sets task status to PENDING and clears actual start/end timestamps.
    This allows resetting a task that was started by mistake.

    This use case inherits common status change logic from StatusChangeUseCase
    and uses the _before_status_change hook to clear time tracking data.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return PENDING as the target status.

        Returns:
            TaskStatus.PENDING
        """
        return TaskStatus.PENDING

    def _before_status_change(self, task: Task) -> None:
        """Clear time tracking fields before pausing.

        Args:
            task: Task that will be paused
        """
        self.time_tracker.clear_time_on_pause(task)
