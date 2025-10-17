"""Use case for archiving a task."""

from application.dto.archive_task_input import ArchiveTaskInput
from application.use_cases.status_change_use_case import StatusChangeUseCase
from domain.entities.task import Task, TaskStatus


class ArchiveTaskUseCase(StatusChangeUseCase[ArchiveTaskInput]):
    """Use case for archiving tasks.

    Archives a task for data retention while removing it from active planning.
    This use case:
    - Clears schedule data (daily_allocations)
    - Sets status to ARCHIVED
    - Skips validation (archiving is always allowed)

    This use case inherits common status change logic from StatusChangeUseCase
    and customizes behavior through hooks.
    """

    def _get_target_status(self) -> TaskStatus:
        """Return ARCHIVED as the target status.

        Returns:
            TaskStatus.ARCHIVED
        """
        return TaskStatus.ARCHIVED

    def _should_validate(self) -> bool:
        """Disable validation for archiving.

        Archiving is always allowed regardless of current status,
        so we skip the validation step.

        Returns:
            False to disable validation
        """
        return False

    def _before_status_change(self, task: Task) -> None:
        """Clear schedule data before archiving.

        Archived tasks are removed from active planning,
        so we clear their daily allocations.

        Args:
            task: Task that will be archived
        """
        task.daily_allocations = {}
