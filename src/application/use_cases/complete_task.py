"""Use case for completing a task."""

from application.dto.complete_task_input import CompleteTaskInput
from application.services.task_status_service import TaskStatusService
from application.use_cases.base import UseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import IncompleteChildrenError
from domain.services.task_eligibility_checker import TaskEligibilityChecker
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.task_repository import TaskRepository


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
        self.status_service = TaskStatusService()

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

        # Task from repository always has ID
        assert task.id is not None

        # Check if task can be completed (business rule in domain layer)
        children = self.repository.get_children(task.id)
        if not TaskEligibilityChecker.can_be_completed(task, children):
            incomplete_children = [c for c in children if c.status != TaskStatus.COMPLETED]
            raise IncompleteChildrenError(task.id, incomplete_children)

        # Change status with time tracking
        return self.status_service.change_status_with_tracking(
            task, TaskStatus.COMPLETED, self.time_tracker, self.repository
        )
