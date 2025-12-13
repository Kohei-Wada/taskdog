"""Use case for fixing actual start/end timestamps."""

from taskdog_core.application.dto.fix_actual_times_input import FixActualTimesInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.task_repository import TaskRepository


class FixActualTimesUseCase(UseCase[FixActualTimesInput, TaskOperationOutput]):
    """Use case for correcting actual start/end timestamps.

    Used to correct timestamps after the fact, for historical accuracy.
    This is a separate operation from status changes to maintain data integrity
    and provide a clear audit trail.
    """

    def __init__(self, repository: TaskRepository) -> None:
        """Initialize use case.

        Args:
            repository: Task repository for persistence
        """
        self.repository = repository

    def execute(self, input_dto: FixActualTimesInput) -> TaskOperationOutput:
        """Execute timestamp correction.

        Args:
            input_dto: Fix actual times input data

        Returns:
            TaskOperationOutput with updated task

        Raises:
            TaskNotFoundException: If task not found
            TaskValidationError: If actual_end < actual_start when both are set
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)

        # Apply changes via entity method (validates internally)
        task.fix_actual_times(
            actual_start=input_dto.actual_start,
            actual_end=input_dto.actual_end,
        )

        # Persist
        self.repository.save(task)

        return TaskOperationOutput.from_task(task)
