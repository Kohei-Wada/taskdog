"""Use case for logging actual hours worked on a task."""

from datetime import date

from taskdog_core.application.dto.log_hours_input import LogHoursInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError
from taskdog_core.domain.repositories.task_repository import TaskRepository


class LogHoursUseCase(UseCase[LogHoursInput, TaskOperationOutput]):
    """Use case for logging actual hours worked on a task."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: LogHoursInput) -> TaskOperationOutput:
        """Execute hours logging.

        Args:
            input_dto: Hours logging input data

        Returns:
            TaskOperationOutput DTO containing updated task information with logged hours

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskValidationError: If date format invalid or hours <= 0
        """
        # Get task
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Validate date format (YYYY-MM-DD) and convert to date object
        try:
            date_obj = date.fromisoformat(input_dto.date)
        except ValueError as e:
            raise TaskValidationError(
                f"Invalid date format: {input_dto.date}. Expected YYYY-MM-DD"
            ) from e

        # Validate hours
        if input_dto.hours <= 0:
            raise TaskValidationError(
                f"Hours must be greater than 0, got {input_dto.hours}"
            )

        # Log hours in actual_daily_hours dict
        task.actual_daily_hours[date_obj] = input_dto.hours

        # Save changes
        self.repository.save(task)

        return TaskOperationOutput.from_task(task)
