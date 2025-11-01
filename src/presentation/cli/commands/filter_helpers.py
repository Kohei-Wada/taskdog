"""Helper functions for task filtering in CLI commands."""

from datetime import datetime

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

    Combines multiple filters using the >> operator. All filters that are
    specified must match for a task to be included (AND logic).

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
        NonArchivedFilter() >> StatusFilter(PENDING) >> TagFilter(["work"])

        >>> build_task_filter(all=True, status="completed", tags=["urgent", "bug"], match_all=True)
        StatusFilter(COMPLETED) >> TagFilter(["urgent", "bug"], match_all=True)
    """
    filter_obj: TaskFilter | None = None

    # Archive filter (unless --all is specified)
    if not all:
        filter_obj = NonArchivedFilter()

    # Status filter
    if status:
        status_enum = TaskStatus(status.upper())
        status_filter = StatusFilter(status_enum)
        filter_obj = filter_obj >> status_filter if filter_obj else status_filter

    # Tag filter
    if tags:
        tag_filter = TagFilter(tags, match_all=match_all)
        filter_obj = filter_obj >> tag_filter if filter_obj else tag_filter

    # Date range filter
    if start_date or end_date:
        start_date_obj = start_date.date() if start_date else None
        end_date_obj = end_date.date() if end_date else None
        date_filter = DateRangeFilter(start_date=start_date_obj, end_date=end_date_obj)
        filter_obj = filter_obj >> date_filter if filter_obj else date_filter

    return filter_obj
