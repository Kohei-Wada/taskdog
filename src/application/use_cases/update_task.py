"""Use case for updating a task."""

from application.dto.update_task_input import UpdateTaskInput
from application.use_cases.base import UseCase
from application.validators.validator_registry import TaskFieldValidatorRegistry
from domain.entities.task import Task
from domain.repositories.task_repository import TaskRepository
from domain.services.time_tracker import TimeTracker


class UpdateTaskUseCase(UseCase[UpdateTaskInput, tuple[Task, list[str]]]):
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
        self.validator_registry = TaskFieldValidatorRegistry(repository)

    def _update_status(
        self,
        task: Task,
        input_dto: UpdateTaskInput,
        updated_fields: list[str],
    ) -> None:
        """Update task status with time tracking.

        Args:
            task: Task to update
            input_dto: Update input data
            updated_fields: List to append field name to
        """
        if input_dto.status is not None:
            # Validate status transition
            self.validator_registry.validate_field("status", input_dto.status, task)

            self.time_tracker.record_time_on_status_change(task, input_dto.status)
            task.status = input_dto.status
            updated_fields.append("status")

    def _update_standard_fields(
        self,
        task: Task,
        input_dto: UpdateTaskInput,
        updated_fields: list[str],
    ) -> None:
        """Update standard fields (name, priority, planned times, deadline, estimated_duration, is_fixed, tags).

        Args:
            task: Task to update
            input_dto: Update input data
            updated_fields: List to append field names to
        """
        field_mapping = {
            "name": input_dto.name,
            "priority": input_dto.priority,
            "planned_start": input_dto.planned_start,
            "planned_end": input_dto.planned_end,
            "deadline": input_dto.deadline,
            "estimated_duration": input_dto.estimated_duration,
            "is_fixed": input_dto.is_fixed,
            "tags": input_dto.tags,
        }

        for field_name, value in field_mapping.items():
            if value is not None:
                # Validate field if validator exists
                self.validator_registry.validate_field(field_name, value, task)
                setattr(task, field_name, value)
                updated_fields.append(field_name)

        # Clear daily_allocations when manually setting planned schedule
        # This ensures manual scheduling takes precedence over optimizer-generated allocations
        if (
            "planned_start" in updated_fields or "planned_end" in updated_fields
        ) and task.daily_allocations:
            task.daily_allocations = {}
            updated_fields.append("daily_allocations")

    def execute(self, input_dto: UpdateTaskInput) -> tuple[Task, list[str]]:
        """Execute task update.

        Args:
            input_dto: Task update input data

        Returns:
            Tuple of (updated task, list of updated field names)

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)
        updated_fields: list[str] = []

        # Update each field type using specialized methods
        self._update_status(task, input_dto, updated_fields)
        self._update_standard_fields(task, input_dto, updated_fields)

        # Save changes
        if updated_fields:
            self.repository.save(task)

        return task, updated_fields
