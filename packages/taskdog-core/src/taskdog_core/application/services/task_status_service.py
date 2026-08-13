"""Service for handling task status changes with time tracking."""

from datetime import datetime

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.repositories.task_repository import TaskRepository


class TaskStatusService:
    """Service for managing task status changes.

    This service encapsulates the common pattern of changing a task's status:
    1. Update task status (via Task entity methods with time tracking)
    2. Save task to repository

    This ensures consistent behavior across all status change operations
    and reduces code duplication in use cases.
    """

    def apply_status_change(self, task: Task, new_status: TaskStatus) -> Task:
        """Apply a status change with time tracking, without persisting.

        Use this when the caller owns persistence (e.g. UpdateTaskUseCase,
        which saves once after all fields are updated).

        Args:
            task: Task to update
            new_status: New status to set

        Returns:
            The same task instance, with status and timestamps updated
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
            task.pause()

        return task

    def change_status_with_tracking(
        self,
        task: Task,
        new_status: TaskStatus,
        repository: TaskRepository,
    ) -> Task:
        """Change task status with automatic time tracking and persistence.

        This method handles the complete workflow of status changes:
        - Updates the task's status via entity methods (which handle timestamps)
        - Persists the changes to the repository

        Args:
            task: Task to update
            new_status: New status to set
            repository: Repository for persisting changes

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
        self.apply_status_change(task, new_status)
        repository.save(task)

        return task
