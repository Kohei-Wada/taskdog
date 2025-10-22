"""Sorter for tasks."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from domain.entities.task import Task
from shared.constants import SORT_SENTINEL_FUTURE
from shared.utils.date_utils import parse_date


class TaskSorter:
    """Sort tasks by multiple criteria.

    Supports sorting by different keys:
    - id: Task ID (ascending by default)
    - priority: Priority level (descending by default - higher priority first)
    - deadline: Deadline date (ascending by default - earlier deadlines first)
    - name: Task name (alphabetical, ascending by default)
    - status: Task status (alphabetical, ascending by default)
    - planned_start: Planned start date (ascending by default)

    Tasks with None values are sorted last for date/time fields.
    """

    def sort(
        self, tasks: list[Task], sort_by: str = "deadline", reverse: bool = False
    ) -> list[Task]:
        """Sort tasks by specified key.

        Args:
            tasks: List of tasks to sort
            sort_by: Sort key (id, priority, deadline, name, status, planned_start)
            reverse: Reverse sort order (default: False)

        Returns:
            Sorted list of tasks

        Raises:
            ValueError: If sort_by is not a valid sort key
        """
        valid_keys = ["id", "priority", "deadline", "name", "status", "planned_start"]
        if sort_by not in valid_keys:
            raise ValueError(f"Invalid sort_by: {sort_by}. Must be one of {valid_keys}")

        # Get the appropriate sort key function
        key_func = self._get_sort_key_function(sort_by)

        # Sort with the key function
        # Note: For priority, we want higher values first by default (reverse=True internally)
        # The reverse parameter inverts this behavior
        if sort_by == "priority":
            # Priority defaults to descending (reverse=True)
            # If user passes reverse=True, we want ascending (reverse=False)
            return sorted(tasks, key=key_func, reverse=not reverse)
        else:
            return sorted(tasks, key=key_func, reverse=reverse)

    def _get_sort_key_function(self, sort_by: str) -> Callable[[Task], Any]:
        """Get the sort key function for the specified sort key.

        Args:
            sort_by: Sort key name

        Returns:
            Function that extracts the sort key from a task
        """
        if sort_by == "id":
            return lambda task: task.id

        elif sort_by == "priority":
            return lambda task: task.priority

        elif sort_by == "deadline":
            return lambda task: self._parse_date_for_sort(task.deadline)

        elif sort_by == "name":
            return lambda task: task.name.lower()  # Case-insensitive sort

        elif sort_by == "status":
            return lambda task: task.status.value

        elif sort_by == "planned_start":
            return lambda task: self._parse_date_for_sort(task.planned_start)

    def _parse_date_for_sort(self, date_str: str | None) -> datetime:
        """Parse a date string for sorting, with None values sorted last.

        Args:
            date_str: Date string to parse (or None)

        Returns:
            datetime object (far future date if None)
        """
        if not date_str:
            return SORT_SENTINEL_FUTURE

        parsed_date = parse_date(date_str)
        if parsed_date is None:
            return SORT_SENTINEL_FUTURE
        # Convert date to datetime for consistent comparison
        return datetime.combine(parsed_date, datetime.min.time())
