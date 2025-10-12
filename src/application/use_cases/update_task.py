"""Use case for updating a task."""

from typing import Tuple, List
from application.use_cases.base import UseCase
from application.dto.update_task_input import UpdateTaskInput
from infrastructure.persistence.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker
from domain.entities.task import Task


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
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        updated_fields = []

        # Handle status separately for time tracking
        if input_dto.status is not None:
            self.time_tracker.record_time_on_status_change(task, input_dto.status)
            task.status = input_dto.status
            updated_fields.append("status")

        # Update remaining fields using dictionary mapping
        field_mapping = {
            "priority": input_dto.priority,
            "planned_start": input_dto.planned_start,
            "planned_end": input_dto.planned_end,
            "deadline": input_dto.deadline,
            "estimated_duration": input_dto.estimated_duration,
        }

        for field_name, value in field_mapping.items():
            if value is not None:
                setattr(task, field_name, value)
                updated_fields.append(field_name)

        if updated_fields:
            self.repository.save(task)

        return task, updated_fields
