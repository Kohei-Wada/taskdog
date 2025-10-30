"""Helper functions for task filtering in CLI commands."""

from datetime import datetime

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.date_range_filter import DateRangeFilter
from application.queries.filters.non_archived_filter import NonArchivedFilter
from application.queries.filters.status_filter import StatusFilter
from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task, TaskStatus


def build_task_filter(all: bool, status: str | None) -> TaskFilter | None:
    """Build task filter based on CLI options with AND logic.

    Logic:
    - Default (no options): NonArchivedFilter (is_archived=False, includes all statuses)
    - --all only: No filter (all tasks including archived)
    - --status X only: NonArchivedFilter + StatusFilter(X) (non-archived tasks filtered by status X)
    - --all --status X: StatusFilter(X) only (all tasks including archived, filtered by status X)

    The --all flag controls whether to include archived tasks.
    The --status flag further filters by specific status.

    Args:
        all: If True, include all tasks (including archived)
        status: Status string (case-insensitive), converts to TaskStatus enum

    Returns:
        TaskFilter instance or None (no filter)

    Examples:
        >>> build_task_filter(all=False, status=None)
        NonArchivedFilter()  # All non-archived tasks (any status)

        >>> build_task_filter(all=True, status=None)
        None  # All tasks (including archived)

        >>> build_task_filter(all=False, status="pending")
        CompositeFilter([NonArchivedFilter(), StatusFilter(PENDING)])  # Non-archived + PENDING

        >>> build_task_filter(all=True, status="completed")
        StatusFilter(COMPLETED)  # All tasks filtered by COMPLETED
    """
    if status:
        # Status filter specified
        status_enum = TaskStatus(status.upper())
        status_filter = StatusFilter(status_enum)

        if all:
            # --all --status X: Show all tasks (including archived) filtered by status X
            return status_filter
        else:
            # --status X only: Show non-archived tasks filtered by status X
            # This creates AND logic: NonArchivedFilter AND StatusFilter
            return CompositeFilter([NonArchivedFilter(), status_filter])
    elif all:
        # --all only: Show all tasks (no filter)
        return None
    else:
        # Default: Show non-archived only
        return NonArchivedFilter()


def apply_date_range_filter(
    tasks: list[Task], start_date_dt: datetime | None, end_date_dt: datetime | None
) -> list[Task]:
    """Apply date range filter to tasks.

    Converts datetime objects to date and applies DateRangeFilter if either start or end date is provided.

    Args:
        tasks: List of tasks to filter
        start_date_dt: Start datetime (will be converted to date)
        end_date_dt: End datetime (will be converted to date)

    Returns:
        Filtered list of tasks (or original list if no dates provided)

    Examples:
        >>> tasks = [task1, task2, task3]
        >>> apply_date_range_filter(tasks, None, None)
        [task1, task2, task3]  # No filter applied

        >>> apply_date_range_filter(tasks, datetime(2025, 10, 1), datetime(2025, 10, 31))
        [task2]  # Only tasks with dates in October
    """
    start_date = start_date_dt.date() if start_date_dt else None
    end_date = end_date_dt.date() if end_date_dt else None

    if start_date or end_date:
        date_filter = DateRangeFilter(start_date=start_date, end_date=end_date)
        return date_filter.filter(tasks)
    return tasks


def parse_field_list(
    fields_str: str | None, valid_fields: set[str] | None = None
) -> list[str] | None:
    """Parse comma-separated field list with optional validation.

    Args:
        fields_str: Comma-separated field string (e.g., "id,name,priority")
        valid_fields: Set of valid field names for validation (optional)

    Returns:
        List of field names, or None if fields_str is None/empty

    Raises:
        ValueError: If any field is not in valid_fields

    Examples:
        >>> parse_field_list("id, name, priority")
        ['id', 'name', 'priority']

        >>> parse_field_list("id,invalid", {"id", "name"})
        ValueError: Invalid field(s): invalid. Valid fields are: id, name
    """
    if not fields_str:
        return None

    # Split by comma and strip whitespace
    field_list = [f.strip() for f in fields_str.split(",")]

    # Validate if valid_fields provided
    if valid_fields:
        invalid_fields = [f for f in field_list if f not in valid_fields]
        if invalid_fields:
            valid_fields_str = ", ".join(sorted(valid_fields))
            raise ValueError(
                f"Invalid field(s): {', '.join(invalid_fields)}. Valid fields are: {valid_fields_str}"
            )

    return field_list
