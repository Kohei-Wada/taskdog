"""Use case for starting a task."""

from application.dto.start_task_input import StartTaskInput
from application.services.task_status_service import TaskStatusService
from application.use_cases.base import UseCase
from domain.entities.task import Task, TaskStatus
from domain.services.task_eligibility_checker import TaskEligibilityChecker
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
            TaskAlreadyFinishedError: If task is already finished
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Task from repository always has ID
        assert task.id is not None

        # Validate task can be started (raises exception if not)
        children = self.repository.get_children(task.id)
        TaskEligibilityChecker.validate_can_be_started(task, children)

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
