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
        # Calculate task counts and total hours
        new_count, rescheduled_count = self._count_task_types(
            modified_tasks, task_states_before
        )
        total_hours = self._calculate_total_hours(modified_tasks)

        # Check for deadline conflicts
        deadline_conflicts = self._count_deadline_conflicts(modified_tasks)

        # Calculate date range span
        days_span = self._calculate_days_span(modified_tasks)

        return new_count, rescheduled_count, total_hours, deadline_conflicts, days_span

    def _count_task_types(
        self, tasks: list[Task], task_states_before: dict[int, datetime | None]
    ) -> tuple[int, int]:
        """Count how many tasks are new vs rescheduled.

        Args:
            tasks: Tasks to analyze
            task_states_before: Previous task states (planned_start before optimization)

        Returns:
            Tuple of (new_count, rescheduled_count)
        """
        new_count = 0
        rescheduled_count = 0

        for task in tasks:
            if task.id not in task_states_before:
                continue

            if task_states_before[task.id] is None:
                new_count += 1
            else:
                rescheduled_count += 1

        return new_count, rescheduled_count

    def _calculate_total_hours(self, tasks: list[Task]) -> float:
        """Calculate total estimated hours across all tasks.

        Args:
            tasks: Tasks to sum hours for

        Returns:
            Total estimated hours
        """
        return sum(task.estimated_duration or 0.0 for task in tasks)

    def _count_deadline_conflicts(self, tasks: list[Task]) -> int:
        """Count tasks where planned_end exceeds deadline.

        Args:
            tasks: Tasks to check for conflicts

        Returns:
            Number of deadline conflicts
        """
        conflicts = 0
        for task in tasks:
            if task.deadline and task.planned_end and task.planned_end > task.deadline:
                conflicts += 1
        return conflicts

    def _calculate_days_span(self, tasks: list[Task]) -> int:
        """Calculate the span of days from earliest start to latest end.

        Args:
            tasks: Tasks to calculate date range for

        Returns:
            Number of days in the schedule (0 if no tasks have dates)
        """
        start_dates = [t.planned_start for t in tasks if t.planned_start]
        end_dates = [t.planned_end for t in tasks if t.planned_end]

        if not start_dates or not end_dates:
            return 0

        min_date = min(start_dates).date()
        max_date = max(end_dates).date()
        return (max_date - min_date).days + 1

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
        result = []
        for task in unscheduled_tasks:
            assert task.id is not None, (
                f"Task {task.name} has no ID (persisted tasks must have IDs)"
            )
            result.append(TaskSummaryDto(id=task.id, name=task.name))
        return result

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
