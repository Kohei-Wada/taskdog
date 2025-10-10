"""Use case for completing a task."""

from application.use_cases.base import UseCase
from application.dto.complete_task_input import CompleteTaskInput
from infrastructure.persistence.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException


class CompleteTaskUseCase(UseCase[CompleteTaskInput, Task]):
    """Use case for completing a task.

    Sets task status to COMPLETED and records actual end time.
    """

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker for recording timestamps
        """
        self.repository = repository
        self.time_tracker = time_tracker

    def execute(self, input_dto: CompleteTaskInput) -> Task:
        """Execute task completion.

        Args:
            input_dto: Task completion input data

        Returns:
            Updated task with COMPLETED status

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self.repository.get_by_id(input_dto.task_id)
        if not task:
            raise TaskNotFoundException(input_dto.task_id)

        # Record time based on status change
        self.time_tracker.record_time_on_status_change(task, TaskStatus.COMPLETED)

        task.status = TaskStatus.COMPLETED
        self.repository.save(task)

        return task
