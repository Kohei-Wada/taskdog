"""Filter for tasks by date range."""

from datetime import date

from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task


class DateRangeFilter(TaskFilter):
    """Filter tasks by date range.

    Returns tasks that have any date field (planned_start, planned_end,
    actual_start, actual_end, deadline) within the specified range.

    If only start_date is provided, filters tasks with dates >= start_date.
    If only end_date is provided, filters tasks with dates <= end_date.
    If both are provided, filters tasks with dates in [start_date, end_date].
    """

    def __init__(self, start_date: date | None = None, end_date: date | None = None):
        """Initialize filter with date range.

        Args:
            start_date: Optional start date (inclusive)
            end_date: Optional end date (inclusive)
        """
        if start_date is None and end_date is None:
            raise ValueError("At least one of start_date or end_date must be provided")

        self.start_date = start_date
        self.end_date = end_date

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks by date range.

        A task is included if any of its date fields (planned_start, planned_end,
        actual_start, actual_end, deadline) falls within the specified range.

        Args:
            tasks: List of all tasks

        Returns:
            List of tasks with dates in the specified range
        """
        filtered = []
        for task in tasks:
            # Collect all date fields from the task
            task_dates = []
            for dt in [
                task.planned_start,
                task.planned_end,
                task.actual_start,
                task.actual_end,
                task.deadline,
            ]:
                if dt:
                    task_dates.append(dt.date())

            # Skip tasks with no dates
            if not task_dates:
                continue

            # Check if any date falls within the range
            if self._has_date_in_range(task_dates):
                filtered.append(task)

        return filtered

    def _has_date_in_range(self, dates: list[date]) -> bool:
        """Check if any date falls within the specified range.

        Args:
            dates: List of dates to check

        Returns:
            True if any date is in range, False otherwise
        """
        for d in dates:
            # Check start_date constraint
            if self.start_date and d < self.start_date:
                continue

            # Check end_date constraint
            if self.end_date and d > self.end_date:
                continue

            # Date passes both constraints
            return True

        return False
