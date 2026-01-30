"""Base workload calculator for calculating daily workload from tasks."""

from datetime import date, timedelta

from taskdog_core.application.queries.workload._strategies import (
    WeekdayOnlyStrategy,
    WorkloadCalculationStrategy,
)
from taskdog_core.domain.entities.task import Task


class BaseWorkloadCalculator:
    """Base class for calculating daily workload from tasks with estimated duration.

    Uses a WorkloadCalculationStrategy to determine how to distribute hours
    when daily_allocations is not explicitly set.

    This is the base class that provides core workload calculation logic.
    For typical use cases, prefer using the specialized calculators:
    - OptimizationWorkloadCalculator: For schedule optimization
    - DisplayWorkloadCalculator: For Gantt charts and reports
    """

    def __init__(self, strategy: WorkloadCalculationStrategy | None = None):
        """Initialize the workload calculator.

        Args:
            strategy: Strategy for computing workload from planned periods.
                     Defaults to WeekdayOnlyStrategy for backward compatibility.
        """
        self.strategy = strategy or WeekdayOnlyStrategy()

    def calculate_daily_workload(
        self, tasks: list[Task], start_date: date, end_date: date
    ) -> dict[date, float]:
        """Calculate daily workload from tasks, excluding weekends and completed tasks.

        This method uses the daily_allocations field if available (set by optimization),
        otherwise falls back to equal distribution across weekdays in the planned period.

        Args:
            tasks: List of all tasks
            start_date: Start date of the calculation period
            end_date: End date of the calculation period

        Returns:
            Dictionary mapping date to total estimated hours {date: hours}
        """
        # Initialize workload dictionary with zeros for all dates
        days = (end_date - start_date).days + 1
        daily_workload: dict[date, float] = {
            start_date + timedelta(days=i): 0.0 for i in range(days)
        }

        # Process each task and accumulate hours
        for task in tasks:
            # Skip tasks that should not be included in workload
            if not (
                task.should_count_in_workload()
                and task.estimated_duration is not None
                and task.planned_start is not None
                and task.planned_end is not None
            ):
                continue

            # Get daily hours for this task
            task_daily_hours = self._task_to_daily_hours(task)

            # Accumulate hours for each date
            for task_date, hours in task_daily_hours.items():
                if task_date in daily_workload:
                    daily_workload[task_date] += hours

        return daily_workload

    def get_task_daily_hours(self, task: Task) -> dict[date, float]:
        """Get daily hour allocations for a single task.

        Public method for external use. Uses daily_allocations if available,
        otherwise distributes evenly across weekdays in the planned period.

        Args:
            task: Task to get daily hours for

        Returns:
            Dictionary mapping date to hours {date: hours}
        """
        return self._task_to_daily_hours(task)

    def _task_to_daily_hours(self, task: Task) -> dict[date, float]:
        """Convert a task to daily hour allocations.

        Uses daily_allocations if available, otherwise distributes evenly across weekdays.

        Args:
            task: Task to convert

        Returns:
            Dictionary mapping date to hours {date: hours}
        """
        if task.daily_allocations:
            return self._compute_from_allocations(task)
        return self._compute_from_planned_period(task)

    def _compute_from_allocations(self, task: Task) -> dict[date, float]:
        """Compute daily hours from task's daily_allocations field.

        Args:
            task: Task with daily_allocations

        Returns:
            Dictionary mapping date to hours {date: hours}
        """
        # daily_allocations is already dict[date, float], just return it
        return task.daily_allocations.copy()

    def _compute_from_planned_period(self, task: Task) -> dict[date, float]:
        """Compute daily hours using the configured strategy.

        Delegates to the strategy to determine how hours should be distributed
        across the planned period (e.g., weekdays only vs. all days).

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping date to hours {date: hours}
        """
        return self.strategy.compute_from_planned_period(task)
