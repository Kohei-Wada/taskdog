"""Composite filter for combining multiple filters with AND logic.

.. deprecated::
    Use the >> operator instead of CompositeFilter directly.
    CompositeFilter is still used internally but direct instantiation
    is discouraged. This class may be made private in future versions.
"""

from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task


class CompositeFilter(TaskFilter):
    """Composite filter that applies multiple filters in sequence (AND logic).

    .. deprecated::
        Use the >> operator to compose filters instead:
        ``filter1 >> filter2 >> filter3``

        Direct use of CompositeFilter is discouraged and may be removed
        in future versions. The >> operator provides a more ergonomic
        and readable way to compose filters.

    Each filter is applied to the result of the previous filter, effectively
    creating an AND relationship between all filters.

    Example (deprecated):
        >>> incomplete_filter = IncompleteFilter()
        >>> status_filter = StatusFilter(TaskStatus.PENDING)
        >>> composite = CompositeFilter([incomplete_filter, status_filter])
        >>> # Returns tasks that are both incomplete AND pending

    Preferred approach:
        >>> incomplete_filter = IncompleteFilter()
        >>> status_filter = StatusFilter(TaskStatus.PENDING)
        >>> composite = incomplete_filter >> status_filter
        >>> # Returns tasks that are both incomplete AND pending
    """

    def __init__(self, filters: list[TaskFilter]):
        """Initialize composite filter with a list of filters.

        Args:
            filters: List of TaskFilter instances to apply in sequence
        """
        self.filters = filters

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Apply all filters in sequence (AND logic).

        Args:
            tasks: List of all tasks to filter

        Returns:
            Tasks that pass all filters
        """
        result = tasks
        for f in self.filters:
            result = f.filter(result)
        return result
