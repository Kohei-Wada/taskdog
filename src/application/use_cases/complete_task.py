"""Use case for completing a task."""

from application.use_cases.base import UseCase
from application.dto.complete_task_input import CompleteTaskInput
from infrastructure.persistence.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import IncompleteChildrenError


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
            IncompleteChildrenError: If task has incomplete children
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Check if all children are completed
        children = self.repository.get_children(task.id)
        incomplete_children = [
            child for child in children if child.status != TaskStatus.COMPLETED
        ]

        if incomplete_children:
            raise IncompleteChildrenError(task.id, incomplete_children)

        # Record time based on status change
        self.time_tracker.record_time_on_status_change(task, TaskStatus.COMPLETED)

        task.status = TaskStatus.COMPLETED
        self.repository.save(task)

        return task
