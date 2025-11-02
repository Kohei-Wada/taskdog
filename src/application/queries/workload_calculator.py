"""Domain service for calculating workload from tasks."""

from collections.abc import Iterable
from datetime import date, timedelta

from domain.entities.task import Task


class WorkloadCalculator:
    """Calculates daily workload from tasks with estimated duration."""

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
        empty_workload = self._initialize_daily_workload(start_date, end_date)
        schedulable_tasks = filter(self._should_include_in_workload, tasks)
        task_allocations = map(self._task_to_daily_hours, schedulable_tasks)
        return self._merge_allocations(empty_workload, task_allocations)

    def _initialize_daily_workload(self, start_date: date, end_date: date) -> dict[date, float]:
        """Initialize daily workload dictionary with zeros for the date range."""
        days = (end_date - start_date).days + 1
        return {start_date + timedelta(days=i): 0.0 for i in range(days)}

    def _should_include_in_workload(self, task: Task) -> bool:
        """Check if a task should be included in workload calculation.

        Returns:
            True if task should be counted in workload, False otherwise
        """
        return (
            task.should_count_in_workload()
            and task.estimated_duration is not None
            and task.planned_start is not None
            and task.planned_end is not None
        )

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
        """Compute daily hours by distributing evenly across all days in planned period.

        For manually scheduled tasks (without daily_allocations), distributes hours
        across all days including weekends. For optimizer-generated schedules,
        use daily_allocations which already exclude weekends.

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping date to hours {date: hours}
        """
        if not (task.planned_start and task.planned_end and task.estimated_duration):
            return {}

        planned_start = task.planned_start.date()
        planned_end = task.planned_end.date()

        # Calculate total days (including weekends)
        total_days = (planned_end - planned_start).days + 1
        if total_days == 0:
            return {}

        hours_per_day = task.estimated_duration / total_days

        # Distribute evenly across ALL days (including weekends)
        result: dict[date, float] = {}
        current_date = planned_start
        while current_date <= planned_end:
            result[current_date] = hours_per_day
            current_date += timedelta(days=1)

        return result

    def _merge_allocations(
        self, base: dict[date, float], allocations: Iterable[dict[date, float]]
    ) -> dict[date, float]:
        """Merge multiple daily allocations into base workload.

        Args:
            base: Base workload dictionary (will not be modified)
            allocations: Iterator of allocation dictionaries to merge

        Returns:
            New dictionary with merged allocations
        """
        result = base.copy()
        for allocation in allocations:
            for task_date, hours in allocation.items():
                if task_date in result:
                    result[task_date] += hours
        return result
