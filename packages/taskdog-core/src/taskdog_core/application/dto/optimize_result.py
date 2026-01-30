"""Result of optimization strategies."""

from dataclasses import dataclass, field
from datetime import date

from taskdog_core.application.dto.optimization_output import SchedulingFailure
from taskdog_core.application.dto.task_dto import TaskSummaryDto
from taskdog_core.domain.entities.task import Task


@dataclass
class OptimizeResult:
    """Result of a schedule optimization operation.

    This dataclass encapsulates the complete output from an optimization strategy,
    including successfully scheduled tasks, failures, and allocation data.

    Attributes:
        tasks: List of tasks with updated schedules
        failures: List of scheduling failures with reasons
        daily_allocations: Mapping of dates to allocated hours
    """

    tasks: list[Task] = field(default_factory=list)
    failures: list[SchedulingFailure] = field(default_factory=list)
    daily_allocations: dict[date, float] = field(default_factory=dict)

    def record_failure(self, task: Task, reason: str) -> None:
        """Record a task scheduling failure with a reason.

        Args:
            task: Task that failed to schedule
            reason: Human-readable reason for failure
        """
        if task.id is None:
            raise ValueError("Task must have an ID")
        task_dto = TaskSummaryDto(id=task.id, name=task.name)
        self.failures.append(
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
