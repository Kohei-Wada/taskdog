"""Domain service for calculating workload from tasks."""

from datetime import date, timedelta

from domain.entities.task import Task
from shared.utils.date_utils import count_weekdays, is_weekday


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
        """Compute daily hours by distributing evenly across weekdays in planned period.

        Args:
            task: Task with planned_start, planned_end, and estimated_duration

        Returns:
            Dictionary mapping date to hours {date: hours}
        """
        if not (task.planned_start and task.planned_end and task.estimated_duration):
            return {}

        planned_start = task.planned_start.date()
        planned_end = task.planned_end.date()

        weekday_count = count_weekdays(planned_start, planned_end)
        if weekday_count == 0:
            return {}

        hours_per_day = task.estimated_duration / weekday_count

        result: dict[date, float] = {}
        current_date = planned_start
        while current_date <= planned_end:
            if is_weekday(current_date):
                result[current_date] = hours_per_day
            current_date += timedelta(days=1)

        return result
