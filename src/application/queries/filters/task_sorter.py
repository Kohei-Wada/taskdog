"""Sorter for tasks."""

from datetime import datetime

from domain.entities.task import Task


class TaskSorter:
    """Sort tasks by multiple criteria.

    Default sort order:
    1. Deadline (ascending) - tasks with earlier deadlines first
    2. Priority (descending) - higher priority tasks first
    3. ID (ascending) - lower ID tasks first

    Tasks without deadlines are sorted last.
    """

    def sort(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by deadline -> priority -> id.

        Args:
            tasks: List of tasks to sort

        Returns:
            Sorted list of tasks
        """

        def sort_key(task):
            # Parse deadline (None values go last)
            deadline_date = self._parse_date(task.deadline) if task.deadline else None

            # Use a far future date for None deadlines so they sort last
            deadline_sort_value = deadline_date if deadline_date else datetime(9999, 12, 31).date()

            # Priority (descending, so negate)
            priority_value = -task.priority

            # ID (ascending)
            id_value = task.id

            return (deadline_sort_value, priority_value, id_value)

        return sorted(tasks, key=sort_key)

    def _parse_date(self, datetime_str: str):
        """Parse date from datetime string.

        Args:
            datetime_str: Datetime string in format "YYYY-MM-DD HH:MM:SS"

        Returns:
            datetime.date object or None
        """
        if not datetime_str:
            return None

        # Extract date part (first 10 characters: YYYY-MM-DD)
        date_str = datetime_str[:10]
        return datetime.strptime(date_str, "%Y-%m-%d").date()
