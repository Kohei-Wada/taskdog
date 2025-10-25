"""Helper functions for task filtering in CLI commands."""

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.filters.status_filter import StatusFilter
from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import TaskStatus


def build_task_filter(all: bool, status: str | None) -> TaskFilter | None:
    """Build task filter based on CLI options with AND logic.

    Logic:
    - Default (no options): IncompleteFilter (PENDING, IN_PROGRESS only)
    - --all only: No filter (all tasks including ARCHIVED)
    - --status X only: IncompleteFilter + StatusFilter(X) (incomplete tasks filtered by status X)
    - --all --status X: StatusFilter(X) only (all tasks including ARCHIVED, filtered by status X)

    The --all flag controls whether to include finished tasks (COMPLETED, CANCELED, ARCHIVED).
    The --status flag further filters by specific status.

    Args:
        all: If True, include all tasks (finished + incomplete)
        status: Status string (case-insensitive), converts to TaskStatus enum

    Returns:
        TaskFilter instance or None (no filter)

    Examples:
        >>> build_task_filter(all=False, status=None)
        IncompleteFilter()  # PENDING + IN_PROGRESS only

        >>> build_task_filter(all=True, status=None)
        None  # All tasks

        >>> build_task_filter(all=False, status="pending")
        CompositeFilter([IncompleteFilter(), StatusFilter(PENDING)])  # Incomplete + PENDING

        >>> build_task_filter(all=True, status="archived")
        StatusFilter(ARCHIVED)  # All tasks filtered by ARCHIVED
    """
    if status:
        # Status filter specified
        status_enum = TaskStatus(status.upper())
        status_filter = StatusFilter(status_enum)

        if all:
            # --all --status X: Show all tasks (including ARCHIVED) filtered by status X
            return status_filter
        else:
            # --status X only: Show incomplete tasks filtered by status X
            # This creates AND logic: IncompleteFilter AND StatusFilter
            return CompositeFilter([IncompleteFilter(), status_filter])
    elif all:
        # --all only: Show all tasks (no filter)
        return None
    else:
        # Default: Show incomplete only
        return IncompleteFilter()
