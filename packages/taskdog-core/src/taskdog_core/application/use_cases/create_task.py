"""Use case for creating a task."""

from datetime import date
from typing import TYPE_CHECKING

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.application.queries.workload import DisplayWorkloadCalculator
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.domain.repositories.task_repository import TaskRepository

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class CreateTaskUseCase(UseCase[CreateTaskInput, TaskOperationOutput]):
    """Use case for creating a new task with auto-generated ID."""

    def __init__(
        self,
        repository: TaskRepository,
        holiday_checker: "IHolidayChecker | None" = None,
    ):
        """Initialize use case with repository.

        Args:
            repository: Task repository for data access
            holiday_checker: Optional holiday checker for excluding holidays
                           from daily allocation calculations
        """
        self.repository = repository
        self._workload_calculator = DisplayWorkloadCalculator(
            holiday_checker=holiday_checker
        )

    def execute(self, input_dto: CreateTaskInput) -> TaskOperationOutput:
        """Execute task creation.

        Args:
            input_dto: Task creation input data

        Returns:
            TaskOperationOutput DTO containing created task information

        Note:
            If planned_start, planned_end, and estimated_duration are all set,
            daily_allocations is automatically calculated using ActualScheduleStrategy.
            This enables SQL aggregation for workload calculations.
        """
        # Calculate daily_allocations if all required fields are present
        daily_allocations = self._calculate_daily_allocations(input_dto)

        # Create task via repository (ID auto-assigned)
        task = self.repository.create(
            name=input_dto.name,
            priority=input_dto.priority,
            planned_start=input_dto.planned_start,
            planned_end=input_dto.planned_end,
            deadline=input_dto.deadline,
            estimated_duration=input_dto.estimated_duration,
            is_fixed=input_dto.is_fixed,
            tags=input_dto.tags or [],
            daily_allocations=daily_allocations,
        )

        return TaskOperationOutput.from_task(task)

    def _calculate_daily_allocations(
        self, input_dto: CreateTaskInput
    ) -> dict[date, float]:
        """Calculate daily_allocations if all required fields are present.

        Args:
            input_dto: Task creation input data

        Returns:
            Dictionary mapping dates to hours, or empty dict if fields are missing
        """
        if not (
            input_dto.planned_start
            and input_dto.planned_end
            and input_dto.estimated_duration
        ):
            return {}

        # Create a temporary task-like object to calculate allocations
        # We need planned_start, planned_end, and estimated_duration
        from dataclasses import dataclass
        from datetime import datetime

        @dataclass
        class TempTask:
            planned_start: datetime
            planned_end: datetime
            estimated_duration: float
            daily_allocations: dict[date, float]

        temp_task = TempTask(
            planned_start=input_dto.planned_start,
            planned_end=input_dto.planned_end,
            estimated_duration=input_dto.estimated_duration,
            daily_allocations={},
        )

        return self._workload_calculator.get_task_daily_hours(temp_task)  # type: ignore[arg-type]
