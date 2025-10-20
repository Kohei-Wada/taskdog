"""Use case for logging actual hours worked on a task."""

from datetime import datetime

from application.dto.log_hours_input import LogHoursInput
from application.use_cases.base import UseCase
from domain.entities.task import Task
from domain.exceptions.task_exceptions import TaskValidationError
from infrastructure.persistence.task_repository import TaskRepository


class LogHoursUseCase(UseCase[LogHoursInput, Task]):
    """Use case for logging actual hours worked on a task."""

    def __init__(self, repository: TaskRepository):
        """Initialize use case with repository.

        Args:
            repository: Task repository for data access
        """
        self.repository = repository

    def execute(self, input_dto: LogHoursInput) -> Task:
        """Execute hours logging.

        Args:
            input_dto: Hours logging input data

        Returns:
            Updated task with logged hours

        Raises:
            TaskNotFoundException: If task doesn't exist
            TaskValidationError: If date format invalid or hours <= 0
        """
        # Get task
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Validate date format (YYYY-MM-DD)
        try:
            datetime.strptime(input_dto.date, "%Y-%m-%d")
        except ValueError as e:
            raise TaskValidationError(
                f"Invalid date format: {input_dto.date}. Expected YYYY-MM-DD"
            ) from e

        # Validate hours
        if input_dto.hours <= 0:
            raise TaskValidationError(f"Hours must be greater than 0, got {input_dto.hours}")

        # Log hours in actual_daily_hours dict
        task.actual_daily_hours[input_dto.date] = input_dto.hours

        # Save changes
        self.repository.save(task)

        return task
