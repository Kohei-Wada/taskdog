"""Use case for starting a task."""

from application.use_cases.base import UseCase
from application.dto.start_task_input import StartTaskInput
from infrastructure.persistence.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException


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

    def execute(self, input_dto: StartTaskInput) -> Task:
        """Execute task start.

        Args:
            input_dto: Task start input data

        Returns:
            Updated task with IN_PROGRESS status

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self.repository.get_by_id(input_dto.task_id)
        if not task:
            raise TaskNotFoundException(input_dto.task_id)

        # Record time based on status change
        self.time_tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)

        task.status = TaskStatus.IN_PROGRESS
        self.repository.save(task)

        return task
