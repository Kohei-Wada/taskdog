"""Use case for updating a task."""

from dataclasses import replace
from datetime import datetime
from typing import TYPE_CHECKING

from taskdog_core.application.dto.update_task_input import UpdateTaskInput
from taskdog_core.application.dto.update_task_output import TaskUpdateOutput
from taskdog_core.application.queries.workload._strategies import ActualScheduleStrategy
from taskdog_core.application.use_cases.base import UseCase
from taskdog_core.application.validators.validator_registry import (
    TaskFieldValidatorRegistry,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.repositories.task_repository import TaskRepository

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


class UpdateTaskUseCase(UseCase[UpdateTaskInput, TaskUpdateOutput]):
    """Use case for updating task properties.

    Supports updating multiple fields and handles time tracking for status changes.
    Returns the updated task and list of updated field names.
    """

    def __init__(
        self,
        repository: TaskRepository,
        holiday_checker: "IHolidayChecker | None" = None,
    ):
        """Initialize use case.

        Args:
            repository: Task repository for data access
            holiday_checker: Optional holiday checker for excluding holidays
                           from daily allocation calculations
        """
        self.repository = repository
        self.validator_registry = TaskFieldValidatorRegistry(repository)
        self._strategy = ActualScheduleStrategy(holiday_checker=holiday_checker)

    def _update_status(
        self,
        task: Task,
        input_dto: UpdateTaskInput,
        updated_fields: list[str],
    ) -> None:
        """Update task status with time tracking via Task entity methods.

        Args:
            task: Task to update
            input_dto: Update input data
            updated_fields: List to append field name to
        """
        if input_dto.status is not None:
            # Validate status transition
            self.validator_registry.validate_field("status", input_dto.status, task)

            # Use Task entity methods for status changes (encapsulation)
            timestamp = datetime.now()
            if input_dto.status == TaskStatus.IN_PROGRESS:
                task.start(timestamp)
            elif input_dto.status == TaskStatus.COMPLETED:
                task.complete(timestamp)
            elif input_dto.status == TaskStatus.CANCELED:
                task.cancel(timestamp)
            elif input_dto.status == TaskStatus.PENDING:
                # For update command, preserve timestamps by default (don't clear)
                task.status = TaskStatus.PENDING

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

        # Recalculate daily_allocations when schedule-affecting fields change
        # This handles both clearing old allocations and computing new ones
        schedule_fields_changed = any(
            f in updated_fields
            for f in ("planned_start", "planned_end", "estimated_duration")
        )
        if schedule_fields_changed:
            self._recalculate_daily_allocations(task, updated_fields)

    def _recalculate_daily_allocations(
        self, task: Task, updated_fields: list[str]
    ) -> None:
        """Recalculate daily_allocations based on current task fields.

        If all required fields (planned_start, planned_end, estimated_duration) are present,
        recalculates daily_allocations using ActualScheduleStrategy. Otherwise clears them.

        Args:
            task: Task to update
            updated_fields: List to append field name to if allocations change
        """
        old_allocations = (
            task.daily_allocations.copy() if task.daily_allocations else {}
        )

        if task.planned_start and task.planned_end and task.estimated_duration:
            # Recalculate allocations based on new schedule
            new_allocations = self._strategy.compute_from_planned_period(task)
            task.set_daily_allocations(new_allocations)
        else:
            # Clear allocations if any required field is missing
            task.set_daily_allocations({})

        # Track if allocations actually changed
        if (
            task.daily_allocations != old_allocations
            and "daily_allocations" not in updated_fields
        ):
            updated_fields.append("daily_allocations")

    def execute(self, input_dto: UpdateTaskInput) -> TaskUpdateOutput:
        """Execute task update.

        Args:
            input_dto: Task update input data

        Returns:
            TaskUpdateOutput DTO containing updated task information and list of updated fields

        Raises:
            TaskNotFoundException: If task doesn't exist
        """
        task = self._get_task_or_raise(self.repository, input_dto.task_id)
        updated_fields: list[str] = []

        # Update each field type using specialized methods
        self._update_status(task, input_dto, updated_fields)
        self._update_standard_fields(task, input_dto, updated_fields)

        # Rebuild task to trigger __post_init__ validation (Always-Valid Entity)
        # This ensures validation is consistent between create and update operations
        if updated_fields:
            task = replace(task)
            self.repository.save(task)

        return TaskUpdateOutput.from_task_and_fields(task, updated_fields)
