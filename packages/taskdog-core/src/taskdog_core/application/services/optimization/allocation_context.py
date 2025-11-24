"""Allocation context for optimization strategies."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING

from taskdog_core.application.dto.optimization_output import SchedulingFailure
from taskdog_core.application.dto.task_dto import TaskSummaryDto
from taskdog_core.application.queries.workload_calculator import WorkloadCalculator
from taskdog_core.domain.entities.task import Task

if TYPE_CHECKING:
    from taskdog_core.domain.services.holiday_checker import IHolidayChecker


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
    - Cleaner strategy classes (pass one object instead of multiple parameters)
    - Better testability (mock one object instead of multiple)
    """

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
        start_date: datetime,
        max_hours_per_day: float,
        holiday_checker: "IHolidayChecker | None" = None,
        current_time: "datetime | None" = None,
        workload_calculator: WorkloadCalculator | None = None,
    ) -> "AllocationContext":
        """Factory method that creates context with initialized allocations.

        This is the recommended way to create an AllocationContext, as it
        automatically initializes daily_allocations from existing task schedules.

        NOTE: The caller is responsible for filtering which tasks to include
        in workload calculation (e.g., excluding tasks that will be rescheduled).

        Args:
            tasks: Tasks to include in workload calculation (already filtered by caller)
            start_date: Starting date for scheduling
            max_hours_per_day: Maximum work hours per day
            holiday_checker: Optional holiday checker
            current_time: Optional current time for time-aware operations
            workload_calculator: Optional pre-configured calculator (injected from UseCase)

        Returns:
            Initialized AllocationContext
        """
        # Initialize allocations from existing tasks
        # Use provided calculator or create default instance
        calculator = workload_calculator or WorkloadCalculator()
        daily_allocations = cls._initialize_allocations(tasks, calculator)

        return cls(
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
        self.record_failure(
            task, "Could not find suitable time slot within constraints"
        )

    @staticmethod
    def _initialize_allocations(
        tasks: list[Task], calculator: "WorkloadCalculator"
    ) -> dict[date, float]:
        """Initialize daily allocations from existing scheduled tasks.

        This is a private helper method for AllocationContext.create().
        It calculates the initial workload distribution by examining
        existing scheduled tasks.

        Args:
            tasks: Tasks to include in workload calculation (already filtered by caller)
            calculator: WorkloadCalculator for calculating task daily hours

        Returns:
            Dictionary mapping dates to allocated hours
        """
        daily_allocations: dict[date, float] = {}

        for task in tasks:
            # Skip tasks without schedules
            if not (task.planned_start and task.estimated_duration):
                continue

            # Get daily allocations for this task
            # Use task.daily_allocations if available, otherwise calculate from WorkloadCalculator
            task_daily_hours = (
                task.daily_allocations or calculator.get_task_daily_hours(task)
            )

            # Add to global daily_allocations
            for date_obj, hours in task_daily_hours.items():
                daily_allocations[date_obj] = (
                    daily_allocations.get(date_obj, 0.0) + hours
                )

        return daily_allocations
