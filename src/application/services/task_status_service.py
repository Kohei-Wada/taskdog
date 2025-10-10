"""Service for handling task status changes with time tracking."""

from domain.entities.task import Task, TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


class TaskStatusService:
    """Service for managing task status changes.

    This service encapsulates the common pattern of changing a task's status:
    1. Record timestamp based on status change (via TimeTracker)
    2. Update task status
    3. Save task to repository

    This ensures consistent behavior across all status change operations
    and reduces code duplication in use cases.
    """

    def change_status_with_tracking(
        self,
        task: Task,
        new_status: TaskStatus,
        time_tracker: TimeTracker,
        repository: TaskRepository,
    ) -> Task:
        """Change task status with automatic time tracking and persistence.

        This method handles the complete workflow of status changes:
        - Records appropriate timestamps (actual_start, actual_end) via TimeTracker
        - Updates the task's status field
        - Persists the changes to the repository

        Args:
            task: Task to update
            new_status: New status to set
            time_tracker: TimeTracker for recording timestamps
            repository: Repository for persisting changes

        Returns:
            Updated task with new status

        Example:
            >>> service = TaskStatusService()
            >>> task = repository.get_by_id(1)
            >>> updated = service.change_status_with_tracking(
            ...     task, TaskStatus.IN_PROGRESS, time_tracker, repository
            ... )
            >>> assert updated.status == TaskStatus.IN_PROGRESS
            >>> assert updated.actual_start is not None
        """
        # Record time based on status change
        time_tracker.record_time_on_status_change(task, new_status)

        # Update status
        task.status = new_status

        # Persist changes
        repository.save(task)

        return task
