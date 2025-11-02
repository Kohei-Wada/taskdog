"""Allocation context for optimization strategies."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

from application.dto.optimization_output import SchedulingFailure
from application.dto.task_dto import TaskSummaryDto
from application.services.optimization.allocation_initializer import AllocationInitializer
from domain.entities.task import Task

if TYPE_CHECKING:
    from domain.repositories.task_repository import TaskRepository
    from domain.services.holiday_checker import IHolidayChecker


@dataclass
class AllocationContext:
    """Context for task allocation operations.

    This dataclass encapsulates all the state and dependencies needed
    for optimization strategies to allocate tasks. It replaces the
    previous approach of using multiple instance variables on the
    strategy class.

    Benefits:
    - Explicit dependencies (easier to understand and test)
    - Immutable context (can be frozen after initialization)
    - Cleaner strategy classes (pass one object instead of 7 parameters)
    - Better testability (mock one object instead of 7)
    """

    repository: "TaskRepository"
    start_date: datetime
    max_hours_per_day: float
    holiday_checker: "IHolidayChecker | None"
    current_time: "datetime | None"
    daily_allocations: dict[date, float] = field(default_factory=dict)
    failed_tasks: list[SchedulingFailure] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        tasks: list[Task],
        repository: "TaskRepository",
        start_date: datetime,
        max_hours_per_day: float,
        force_override: bool,
        holiday_checker: "IHolidayChecker | None" = None,
        current_time: "datetime | None" = None,
    ) -> "AllocationContext":
        """Factory method that creates context with initialized allocations.

        This is the recommended way to create an AllocationContext, as it
        automatically initializes daily_allocations from existing task schedules.

        Args:
            tasks: All tasks in the system
            repository: Task repository
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            force_override: Whether to override existing schedules
            holiday_checker: Optional holiday checker
            current_time: Optional current time for time-aware operations

        Returns:
            Initialized AllocationContext
        """
        # Initialize allocations from existing tasks
        initializer = AllocationInitializer()
        daily_allocations = initializer.initialize_allocations(tasks, force_override)

        return cls(
            repository=repository,
            start_date=start_date,
            max_hours_per_day=max_hours_per_day,
            holiday_checker=holiday_checker,
            current_time=current_time,
            daily_allocations=daily_allocations,
            failed_tasks=[],
        )

    def record_failure(self, task: Task, reason: str) -> None:
        """Record a task scheduling failure with a reason.

        Args:
            task: Task that failed to schedule
            reason: Human-readable reason for failure
        """
        # Convert Task to TaskSummaryDto
        if task.id is None:
            raise ValueError("Task must have an ID")
        task_dto = TaskSummaryDto(id=task.id, name=task.name)
        self.failed_tasks.append(
            SchedulingFailure(
                task=task_dto,
                reason=reason,
            )
        )

    def record_allocation_failure(self, task: Task) -> None:
        """Record a generic allocation failure.

        Args:
            task: Task that failed to allocate
        """
        self.record_failure(task, "Could not find suitable time slot within constraints")
