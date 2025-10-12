"""Domain service for calculating workload from tasks."""

from datetime import date, datetime, timedelta

from domain.entities.task import Task, TaskStatus
from shared.utils.date_utils import DateTimeParser


class WorkloadCalculator:
    """Calculates daily workload from tasks with estimated duration."""

    def calculate_daily_workload(
        self, tasks: list[Task], start_date: date, end_date: date
    ) -> dict[date, float]:
        """Calculate daily workload from tasks, excluding weekends and completed tasks.

        This method uses the daily_allocations field if available (set by ScheduleOptimizer),
        otherwise falls back to equal distribution across weekdays in the planned period.

        Args:
            tasks: List of all tasks
            start_date: Start date of the calculation period
            end_date: End date of the calculation period

        Returns:
            Dictionary mapping date to total estimated hours {date: hours}
        """
        days = (end_date - start_date).days + 1
        daily_workload = {start_date + timedelta(days=i): 0.0 for i in range(days)}

        # Build parent-child map to identify parent tasks
        parent_ids = set()
        for task in tasks:
            if task.parent_id:
                parent_ids.add(task.parent_id)

        # Filter schedulable tasks
        for task in tasks:
            # Skip parent tasks (tasks that have children)
            # Parent tasks are summary tasks and their work is done by children
            if task.id in parent_ids:
                continue
            # Skip completed tasks
            if task.status == TaskStatus.COMPLETED:
                continue

            # Skip tasks without estimated duration
            if not task.estimated_duration:
                continue

            # Use planned dates if available, otherwise skip
            if not (task.planned_start and task.planned_end):
                continue

            # Use daily_allocations if available (from ScheduleOptimizer)
            # Note: Parent tasks don't have daily_allocations, so they will be skipped here
            # and fall through to the else block, which will distribute their estimated_duration
            if task.daily_allocations:
                for date_str, hours in task.daily_allocations.items():
                    try:
                        task_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                        if task_date in daily_workload:
                            daily_workload[task_date] += hours
                    except ValueError:
                        # Skip invalid date strings
                        pass
            else:
                # Fallback: distribute equally across weekdays (for backward compatibility)
                planned_start = DateTimeParser.parse_date(task.planned_start)
                planned_end = DateTimeParser.parse_date(task.planned_end)

                if not (planned_start and planned_end):
                    continue

                # Count weekdays in the task's planned period
                weekday_count = self._count_weekdays(planned_start, planned_end)

                if weekday_count == 0:
                    continue

                # Distribute hours equally across weekdays
                hours_per_day = task.estimated_duration / weekday_count

                # Add to each weekday in the period
                current_date = planned_start
                while current_date <= planned_end:
                    # Skip weekends and add hours to weekdays in range
                    if (
                        current_date.weekday() < 5 and current_date in daily_workload
                    ):  # Monday=0, Friday=4
                        daily_workload[current_date] += hours_per_day
                    current_date += timedelta(days=1)

        return daily_workload

    def _count_weekdays(self, start: date, end: date) -> int:
        """Count weekdays (Monday-Friday) in a date range.

        Args:
            start: Start date (inclusive)
            end: End date (inclusive)

        Returns:
            Number of weekdays in the range
        """
        weekday_count = 0
        current_date = start
        while current_date <= end:
            # Skip weekends (Saturday=5, Sunday=6)
            if current_date.weekday() < 5:
                weekday_count += 1
            current_date += timedelta(days=1)
        return weekday_count
