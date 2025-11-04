"""Service for handling task status changes with time tracking."""

from datetime import datetime

from domain.entities.task import Task, TaskStatus
from domain.repositories.task_repository import TaskRepository


class TaskStatusService:
    """Service for managing task status changes.

    This service encapsulates the common pattern of changing a task's status:
    1. Update task status (via Task entity methods with time tracking)
    2. Save task to repository

    This ensures consistent behavior across all status change operations
    and reduces code duplication in use cases.
    """

    def change_status_with_tracking(
        self,
        task: Task,
        new_status: TaskStatus,
        repository: TaskRepository,
        *,
        clear_timestamps: bool = True,
    ) -> Task:
        """Change task status with automatic time tracking and persistence.

        This method handles the complete workflow of status changes:
        - Updates the task's status via entity methods (which handle timestamps)
        - Persists the changes to the repository

        Args:
            task: Task to update
            new_status: New status to set
            repository: Repository for persisting changes
            clear_timestamps: Whether to clear timestamps when moving to PENDING
                              (True for pause, False for direct status change)

        Returns:
            Updated task with new status

        Example:
            >>> service = TaskStatusService()
            >>> task = repository.get_by_id(1)
            >>> updated = service.change_status_with_tracking(
            ...     task, TaskStatus.IN_PROGRESS, repository
            ... )
            >>> assert updated.status == TaskStatus.IN_PROGRESS
            >>> assert updated.actual_start is not None
        """
        # Update status via Task entity methods (encapsulation)
        timestamp = datetime.now()

        if new_status == TaskStatus.IN_PROGRESS:
            task.start(timestamp)
        elif new_status == TaskStatus.COMPLETED:
            task.complete(timestamp)
        elif new_status == TaskStatus.CANCELED:
            task.cancel(timestamp)
        elif new_status == TaskStatus.PENDING:
            # For PENDING, use pause (clears timestamps) or reopen based on context
            if clear_timestamps:
                task.pause()
            else:
                task.reopen()

        # Persist changes
        repository.save(task)

        return task
