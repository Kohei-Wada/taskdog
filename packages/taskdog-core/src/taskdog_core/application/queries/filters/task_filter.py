"""Base class for task filters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from taskdog_core.domain.entities.task import Task


class TaskFilter(ABC):
    """Abstract base class for task filters.

    Filters apply criteria to select a subset of tasks from a collection.
    Concrete filters implement specific filtering logic (e.g., today's tasks,
    incomplete tasks, tasks within a date range).

    Filters can be composed using the >> operator:
        filter1 >> filter2 >> filter3
    This creates a composite filter that applies all filters in sequence.
    """

    @abstractmethod
    def filter(self, tasks: list[Task]) -> list[Task]:
        """Filter tasks based on specific criteria.

        Args:
            tasks: List of all tasks to filter

        Returns:
            Filtered list of tasks matching the criteria
        """
        pass

    def __rshift__(self, other: TaskFilter | None) -> TaskFilter:
        """Compose filters using the >> operator.

        Creates a composite filter that applies both filters in sequence.
        The left filter is applied first, then the right filter is applied
        to the results.

        Args:
            other: The filter to apply after this one, or None

        Returns:
            A composite filter, or self if other is None

        Examples:
            >>> filter1 = NonArchivedFilter()
            >>> filter2 = StatusFilter(TaskStatus.PENDING)
            >>> combined = filter1 >> filter2
            >>> # Equivalent to: filter2.filter(filter1.filter(tasks))
        """
        if other is None:
            return self

        # Import here to avoid circular dependency
        from taskdog_core.application.queries.filters.composite_filter import (
            CompositeFilter,
        )

        # If self is already a CompositeFilter, extend it
        if isinstance(self, CompositeFilter):
            return CompositeFilter([*self.filters, other])

        # If other is a CompositeFilter, prepend self
        if isinstance(other, CompositeFilter):
            return CompositeFilter([self, *other.filters])

        # Create new CompositeFilter with both filters
        return CompositeFilter([self, other])
