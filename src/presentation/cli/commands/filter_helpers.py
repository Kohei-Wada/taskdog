"""Helper functions for task filtering in CLI commands."""

from datetime import datetime

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.date_range_filter import DateRangeFilter
from application.queries.filters.non_archived_filter import NonArchivedFilter
from application.queries.filters.status_filter import StatusFilter
from application.queries.filters.tag_filter import TagFilter
from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import TaskStatus


def build_task_filter(
    all: bool,
    status: str | None,
    tags: list[str] | None = None,
    match_all: bool = False,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> TaskFilter | None:
    """Build task filter based on CLI options with AND logic.

    Combines multiple filters (archive, status, tags, date range) into a single CompositeFilter
    using AND logic. All filters that are specified must match for a task to be included.

    Archive Logic:
    - Default (all=False): NonArchivedFilter (is_archived=False)
    - --all: No archive filter (includes archived tasks)

    Status Logic:
    - --status X: StatusFilter(X) (filters by specific status)

    Tag Logic:
    - --tag A --tag B (match_all=False): OR logic (has tag A OR tag B)
    - --tag A --tag B --match-all: AND logic (has tag A AND tag B)

    Date Range Logic:
    - --start-date/--end-date: DateRangeFilter (filters by planned/actual dates)

    Args:
        all: If True, include all tasks (including archived)
        status: Status string (case-insensitive), converts to TaskStatus enum
        tags: List of tags to filter by (optional)
        match_all: If True, task must have all tags (AND). If False, at least one tag (OR)
        start_date: Start datetime for date range filter (optional)
        end_date: End datetime for date range filter (optional)

    Returns:
        TaskFilter instance or None (no filter)

    Examples:
        >>> build_task_filter(all=False, status=None)
        NonArchivedFilter()  # All non-archived tasks

        >>> build_task_filter(all=False, status="pending", tags=["work"])
        CompositeFilter([NonArchivedFilter(), StatusFilter(PENDING), TagFilter(["work"])])

        >>> build_task_filter(all=True, status="completed", tags=["urgent", "bug"], match_all=True)
        CompositeFilter([StatusFilter(COMPLETED), TagFilter(["urgent", "bug"], match_all=True)])
    """
    filters: list[TaskFilter] = []

    # Archive filter (unless --all is specified)
    if not all:
        filters.append(NonArchivedFilter())

    # Status filter
    if status:
        status_enum = TaskStatus(status.upper())
        filters.append(StatusFilter(status_enum))

    # Tag filter
    if tags:
        filters.append(TagFilter(tags, match_all=match_all))

    # Date range filter
    if start_date or end_date:
        start_date_obj = start_date.date() if start_date else None
        end_date_obj = end_date.date() if end_date else None
        filters.append(DateRangeFilter(start_date=start_date_obj, end_date=end_date_obj))

    # Return combined filter or None if no filters
    if not filters:
        return None
    elif len(filters) == 1:
        return filters[0]
    else:
        return CompositeFilter(filters)


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
