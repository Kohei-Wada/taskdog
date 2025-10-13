"""Use case for starting a task."""

from application.dto.start_task_input import StartTaskInput
from application.services.task_status_service import TaskStatusService
from application.use_cases.base import UseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskWithChildrenError
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


class StartTaskUseCase(UseCase[StartTaskInput, Task]):
    """Use case for starting a task.

    Sets task status to IN_PROGRESS and records actual start time.
    """

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker for recording timestamps
        """
        self.repository = repository
        self.time_tracker = time_tracker
        self.status_service = TaskStatusService()

    def execute(self, input_dto: StartTaskInput) -> Task:
        """Execute task start.

        Args:
            input_dto: Task start input data

        Returns:
            Updated task with IN_PROGRESS status

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskWithChildrenError: If task has child tasks
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Task from repository always has ID
        assert task.id is not None

        # Check if task has children
        children = self.repository.get_children(task.id)
        if children:
            raise TaskWithChildrenError(task.id, children)

        # Change status with time tracking
        task = self.status_service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )

        # Auto-start all ancestor tasks if they're still pending
        current_parent_id = task.parent_id
        while current_parent_id is not None:
            parent = self.repository.get_by_id(current_parent_id)
            if parent and parent.status == TaskStatus.PENDING:
                self.status_service.change_status_with_tracking(
                    parent, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
                )
            # Move to next ancestor
            current_parent_id = parent.parent_id if parent else None

        return task
