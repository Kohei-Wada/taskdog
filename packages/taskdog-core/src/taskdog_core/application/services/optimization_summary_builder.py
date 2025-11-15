"""Service for building optimization summary from task data."""

from datetime import date, datetime

from taskdog_core.application.dto.optimization_summary import OptimizationSummary
from taskdog_core.application.dto.task_dto import TaskSummaryDto
from taskdog_core.domain.entities.task import Task
from taskdog_core.domain.repositories.task_repository import TaskRepository


class OptimizationSummaryBuilder:
    """Builds optimization summary from modified tasks and repository state.

    This service analyzes optimization results and calculates metrics like
    new/rescheduled task counts, deadline conflicts, and workload violations.
    """

    def __init__(self, repository: TaskRepository):
        """Initialize the summary builder.

        Args:
            repository: Task repository for querying task state
        """
        self.repository = repository

    def _analyze_modified_tasks(
        self,
        modified_tasks: list[Task],
        task_states_before: dict[int, datetime | None],
    ) -> tuple[int, int, float, int, int]:
        """Analyze modified tasks to calculate metrics.

        Args:
            modified_tasks: Tasks that were optimized
            task_states_before: Mapping of task IDs to their planned_start before optimization

        Returns:
            Tuple of (new_count, rescheduled_count, total_hours, deadline_conflicts, days_span)
        """
        new_count = 0
        rescheduled_count = 0
        total_hours = 0.0
        deadline_conflicts = 0

        for task in modified_tasks:
            if task.estimated_duration:
                total_hours += task.estimated_duration

            # Check if this was new or rescheduled
            if task.id in task_states_before:
                if task_states_before[task.id] is None:
                    new_count += 1
                else:
                    rescheduled_count += 1

            # Check deadline conflicts
            if task.deadline and task.planned_end:
                deadline_dt = task.deadline
                end_dt = task.planned_end
                if end_dt > deadline_dt:
                    deadline_conflicts += 1

        # Calculate date range
        start_dates = [t.planned_start for t in modified_tasks if t.planned_start]
        end_dates = [t.planned_end for t in modified_tasks if t.planned_end]

        if start_dates and end_dates:
            min_date = min(start_dates).date()
            max_date = max(end_dates).date()
            days_span = (max_date - min_date).days + 1
        else:
            days_span = 0

        return new_count, rescheduled_count, total_hours, deadline_conflicts, days_span

    def _find_unscheduled_tasks(self) -> list[TaskSummaryDto]:
        """Find tasks that couldn't be scheduled.

        Returns:
            List of TaskSummaryDto for unscheduled tasks
        """
        all_tasks_after = self.repository.get_all()
        unscheduled_tasks = []

        for task in all_tasks_after:
            # Skip finished tasks (COMPLETED or CANCELED)
            if task.is_finished:
                continue
            # Skip tasks without estimated duration
            if not task.estimated_duration:
                continue
            # Check if task has no schedule
            if not task.planned_start:
                unscheduled_tasks.append(task)

        # Convert unscheduled tasks to DTOs
        # Note: Tasks from repository always have IDs (persisted entities)
        return [
            TaskSummaryDto(id=task.id, name=task.name)  # type: ignore[arg-type]
            for task in unscheduled_tasks
        ]

    def _validate_workload(
        self, daily_allocations: dict[date, float], max_hours_per_day: float
    ) -> list[tuple[str, float]]:
        """Identify days where allocated hours exceed the maximum.

        Args:
            daily_allocations: Daily workload allocations (date -> hours)
            max_hours_per_day: Maximum hours per day constraint

        Returns:
            List of (date_str, hours) tuples for overloaded days
        """
        overloaded_days = []
        for date_obj, hours in sorted(daily_allocations.items()):
            if hours > max_hours_per_day:
                overloaded_days.append((date_obj.isoformat(), hours))
        return overloaded_days

    def build(
        self,
        modified_tasks: list[Task],
        task_states_before: dict[int, datetime | None],
        daily_allocations: dict[date, float],
        max_hours_per_day: float,
    ) -> OptimizationSummary:
        """Calculate optimization summary from modified tasks.

        Args:
            modified_tasks: Tasks that were optimized
            task_states_before: Mapping of task IDs to their planned_start before optimization
            daily_allocations: Daily workload allocations (date_str -> hours)
            max_hours_per_day: Maximum hours per day constraint

        Returns:
            OptimizationSummary with calculated metrics
        """
        # Delegate to specialized methods
        (
            new_count,
            rescheduled_count,
            total_hours,
            deadline_conflicts,
            days_span,
        ) = self._analyze_modified_tasks(modified_tasks, task_states_before)

        unscheduled_tasks_dto = self._find_unscheduled_tasks()

        overloaded_days = self._validate_workload(daily_allocations, max_hours_per_day)

        return OptimizationSummary(
            new_count=new_count,
            rescheduled_count=rescheduled_count,
            total_hours=total_hours,
            deadline_conflicts=deadline_conflicts,
            days_span=days_span,
            unscheduled_tasks=unscheduled_tasks_dto,
            overloaded_days=overloaded_days,
        )
