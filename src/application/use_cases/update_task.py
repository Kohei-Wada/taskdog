"""Use case for updating a task."""

from typing import Tuple, List
from application.use_cases.base import UseCase
from application.dto.update_task_input import UpdateTaskInput
from infrastructure.persistence.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskNotFoundException


class UpdateTaskUseCase(UseCase[UpdateTaskInput, Tuple[Task, List[str]]]):
    """Use case for updating task properties.

    Supports updating multiple fields and handles time tracking for status changes.
    Returns the updated task and list of updated field names.
    """

    def __init__(self, repository: TaskRepository, time_tracker: TimeTracker):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            time_tracker: Time tracker for recording timestamps
        """
        self.repository = repository
        self.time_tracker = time_tracker

    def execute(self, input_dto: UpdateTaskInput) -> Tuple[Task, List[str]]:
        """Execute task update.

        Args:
            input_dto: Task update input data

        Returns:
            Tuple of (updated task, list of updated field names)

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self.repository.get_by_id(input_dto.task_id)
        if not task:
            raise TaskNotFoundException(input_dto.task_id)

        updated_fields = []

        # Handle status separately for time tracking
        if input_dto.status is not None:
            self.time_tracker.record_time_on_status_change(task, input_dto.status)
            task.status = input_dto.status
            updated_fields.append("status")

        # Update remaining fields
        if input_dto.priority is not None:
            task.priority = input_dto.priority
            updated_fields.append("priority")

        if input_dto.planned_start is not None:
            task.planned_start = input_dto.planned_start
            updated_fields.append("planned_start")

        if input_dto.planned_end is not None:
            task.planned_end = input_dto.planned_end
            updated_fields.append("planned_end")

        if input_dto.deadline is not None:
            task.deadline = input_dto.deadline
            updated_fields.append("deadline")

        if input_dto.estimated_duration is not None:
            task.estimated_duration = input_dto.estimated_duration
            updated_fields.append("estimated_duration")

        if updated_fields:
            self.repository.save(task)

        return task, updated_fields
