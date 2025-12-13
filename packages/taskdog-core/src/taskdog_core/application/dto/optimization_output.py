"""DTOs for optimization results."""

from dataclasses import dataclass
from datetime import date, datetime

from taskdog_core.application.dto.optimization_summary import OptimizationSummary
from taskdog_core.application.dto.task_dto import TaskSummaryDto


@dataclass
class SchedulingFailure:
    """Information about a task scheduling failure.

    Attributes:
        task: Basic task information (ID and name only)
        reason: Human-readable reason why scheduling failed
    """

    task: TaskSummaryDto
    reason: str


@dataclass
class OptimizationOutput:
    """Complete result of schedule optimization.

    This DTO encapsulates all information from the optimization process,
    including both successful and failed tasks, daily allocations, and
    a summary of the optimization.

    Attributes:
        successful_tasks: Basic info of tasks that were successfully scheduled
        failed_tasks: Tasks that could not be scheduled with reasons
        daily_allocations: Mapping of date objects to allocated hours
        summary: Optimization summary with metrics
        task_states_before: Mapping of task IDs to their planned_start before optimization
    """

    successful_tasks: list[TaskSummaryDto]
    failed_tasks: list[SchedulingFailure]
    daily_allocations: dict[date, float]
    summary: OptimizationSummary
    task_states_before: dict[int, datetime | None]

    def has_failures(self) -> bool:
        """Check if any tasks failed to be scheduled.

        Returns:
            True if at least one task failed to be scheduled
        """
        return len(self.failed_tasks) > 0

    def all_failed(self) -> bool:
        """Check if all schedulable tasks failed.

        Returns:
            True if no tasks were successfully scheduled
        """
        return len(self.successful_tasks) == 0 and len(self.failed_tasks) > 0
