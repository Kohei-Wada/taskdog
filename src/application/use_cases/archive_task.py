"""Use case for archiving a task."""

from application.dto.archive_task_request import ArchiveTaskRequest
from application.use_cases.status_change_use_case import StatusChangeUseCase
from domain.entities.task import Task, TaskStatus


class ArchiveTaskUseCase(StatusChangeUseCase[ArchiveTaskRequest]):
    """Use case for archiving tasks.

    Archives a task for data retention while removing it from active views.
    This use case:
    - Transitions task to ARCHIVED status from any current status
    - Clears schedule data (daily_allocations)
    - Acts as a soft delete mechanism

    Archived tasks are read-only and excluded from default views.
    Use RestoreTaskUseCase to restore an archived task.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return ARCHIVED as the target status.

        Returns:
            TaskStatus.ARCHIVED
        """
        return TaskStatus.ARCHIVED

    def _should_validate(self) -> bool:
        """Skip validation - archiving is allowed from any status.

        Returns:
            False to skip standard validation
        """
        return False

    def _before_status_change(self, task: Task) -> None:
        """Clear schedule data before archiving.

        Args:
            task: Task that will be archived
        """
        # Clear schedule data
        task.daily_allocations = {}
