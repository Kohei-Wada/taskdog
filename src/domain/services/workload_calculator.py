"""Domain service for calculating workload from tasks."""

from datetime import date, datetime, timedelta

from domain.entities.task import Task
from domain.services.task_eligibility_checker import TaskEligibilityChecker
from shared.utils.date_utils import DateTimeParser, count_weekdays


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
        schedulable_tasks = filter(self._is_schedulable_task, tasks)
        task_allocations = map(self._task_to_daily_hours, schedulable_tasks)
        return self._merge_allocations(empty_workload, task_allocations)

    def _initialize_daily_workload(self, start_date: date, end_date: date) -> dict[date, float]:
        """Initialize daily workload dictionary with zeros for the date range."""
        days = (end_date - start_date).days + 1
        return {start_date + timedelta(days=i): 0.0 for i in range(days)}

    def _is_schedulable_task(self, task: Task) -> bool:
        """Check if a task should be included in workload calculation.

        Returns:
            True if task should be counted in workload, False otherwise
        """
        return (
            TaskEligibilityChecker.should_count_in_workload(task)
            and task.estimated_duration is not None
            and task.planned_start is not None
            and task.planned_end is not None
        )

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
        result: dict[date, float] = {}
        for date_str, hours in task.daily_allocations.items():
            try:
                task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                result[task_date] = hours
            except ValueError:
                # Skip invalid date strings
                pass
        return result

    def _compute_from_planned_period(self, task: Task) -> dict[date, float]:
        """Compute daily hours by distributing evenly across weekdays in planned period.

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping date to hours {date: hours}
        """
        planned_start = DateTimeParser.parse_date(task.planned_start)
        planned_end = DateTimeParser.parse_date(task.planned_end)

        if not (planned_start and planned_end and task.estimated_duration):
            return {}

        weekday_count = count_weekdays(planned_start, planned_end)
        if weekday_count == 0:
            return {}

        hours_per_day = task.estimated_duration / weekday_count

        result: dict[date, float] = {}
        current_date = planned_start
        while current_date <= planned_end:
            if current_date.weekday() < 5:  # Monday=0, Friday=4
                result[current_date] = hours_per_day
            current_date += timedelta(days=1)

        return result

    def _merge_allocations(self, base: dict[date, float], allocations: map) -> dict[date, float]:
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
