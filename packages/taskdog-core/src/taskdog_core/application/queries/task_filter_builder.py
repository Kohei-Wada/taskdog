"""Task filter builder service.

This service encapsulates the logic for composing task filters from
query input DTOs, centralizing filter construction logic that was
previously duplicated across API routes.
"""

from __future__ import annotations

from taskdog_core.application.dto.query_inputs import ListTasksInput
from taskdog_core.application.queries.filters.date_range_filter import DateRangeFilter
from taskdog_core.application.queries.filters.non_archived_filter import (
    NonArchivedFilter,
)
from taskdog_core.application.queries.filters.status_filter import StatusFilter
from taskdog_core.application.queries.filters.tag_filter import TagFilter
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import TaskStatus


class TaskFilterBuilder:
    """Builds TaskFilter objects from query input DTOs.

    This service centralizes the filter composition logic, ensuring consistent
    filter construction across all query endpoints (list, gantt).

    The builder follows the Strategy pattern, creating appropriate filter
    compositions based on the input DTO parameters.
    """

    @staticmethod
    def build(input_dto: ListTasksInput) -> TaskFilter | None:
        """Build a TaskFilter from the given input DTO.

        Constructs a composite filter by combining individual filters
        based on the input parameters. Filters are applied in order:
        1. Archive filter (if not include_archived)
        2. Status filter (if status specified)
        3. Tag filter (if tags specified)
        4. Time range / date filter (based on time_range)

        Args:
            input_dto: The query input parameters

        Returns:
            A composed TaskFilter, or None if no filters apply
        """
        filter_obj: TaskFilter | None = None

        # Archive filter
        if not input_dto.include_archived:
            filter_obj = NonArchivedFilter()

        # Status filter
        if input_dto.status:
            try:
                status_filter = StatusFilter(
                    status=TaskStatus[input_dto.status.upper()]
                )
                filter_obj = TaskFilterBuilder._compose(filter_obj, status_filter)
            except KeyError:
                # Invalid status value - skip status filter
                pass

        # Tag filter
        if input_dto.tags:
            tag_filter = TagFilter(
                tags=input_dto.tags,
                match_all=input_dto.match_all_tags,
            )
            filter_obj = TaskFilterBuilder._compose(filter_obj, tag_filter)

        # Time range filter
        filter_obj = TaskFilterBuilder._apply_time_range(filter_obj, input_dto)

        return filter_obj

    @staticmethod
    def _compose(
        existing: TaskFilter | None,
        new_filter: TaskFilter,
    ) -> TaskFilter:
        """Compose two filters, handling None case.

        Args:
            existing: Existing filter (may be None)
            new_filter: New filter to add

        Returns:
            Composed filter
        """
        if existing is None:
            return new_filter
        return existing >> new_filter

    @staticmethod
    def _apply_time_range(
        filter_obj: TaskFilter | None,
        input_dto: ListTasksInput,
    ) -> TaskFilter | None:
        """Apply time range filter based on input DTO.

        Applies DateRangeFilter when custom date range is specified.

        Args:
            filter_obj: Current filter chain
            input_dto: Query input with time range parameters

        Returns:
            Updated filter chain with time filter applied
        """
        # Custom time range with explicit dates
        if input_dto.start_date is not None or input_dto.end_date is not None:
            date_filter = DateRangeFilter(
                start_date=input_dto.start_date,
                end_date=input_dto.end_date,
            )
            return TaskFilterBuilder._compose(filter_obj, date_filter)

        return filter_obj
