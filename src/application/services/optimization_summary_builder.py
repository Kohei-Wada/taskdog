"""Service for building optimization summary from task data."""

from datetime import datetime

from application.dto.optimization_summary import OptimizationSummary
from domain.entities.task import Task
from infrastructure.persistence.task_repository import TaskRepository
from shared.constants.formats import DATETIME_FORMAT


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

    def build(
        self,
        modified_tasks: list[Task],
        task_states_before: dict[int, str | None],
        daily_allocations: dict[str, float],
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
        # Analyze changes
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
                deadline_dt = datetime.strptime(task.deadline, DATETIME_FORMAT)
                end_dt = datetime.strptime(task.planned_end, DATETIME_FORMAT)
                if end_dt > deadline_dt:
                    deadline_conflicts += 1

        # Calculate date range
        start_dates = [
            datetime.strptime(t.planned_start, DATETIME_FORMAT)
            for t in modified_tasks
            if t.planned_start
        ]
        end_dates = [
            datetime.strptime(t.planned_end, DATETIME_FORMAT)
            for t in modified_tasks
            if t.planned_end
        ]

        if start_dates and end_dates:
            min_date = min(start_dates).date()
            max_date = max(end_dates).date()
            days_span = (max_date - min_date).days + 1
        else:
            days_span = 0

        # Check for tasks that couldn't be scheduled
        all_tasks_after = self.repository.get_all()
        unscheduled_tasks = []

        for task in all_tasks_after:
            # Skip deleted and finished tasks
            if task.is_deleted or task.is_finished:
                continue
            # Skip tasks without estimated duration
            if not task.estimated_duration:
                continue
            # Check if task has no schedule
            if not task.planned_start:
                unscheduled_tasks.append(task)

        # Workload validation
        overloaded_days = []
        for date_str, hours in sorted(daily_allocations.items()):
            if hours > max_hours_per_day:
                overloaded_days.append((date_str, hours))

        return OptimizationSummary(
            new_count=new_count,
            rescheduled_count=rescheduled_count,
            total_hours=total_hours,
            deadline_conflicts=deadline_conflicts,
            days_span=days_span,
            unscheduled_tasks=unscheduled_tasks,
            overloaded_days=overloaded_days,
        )
