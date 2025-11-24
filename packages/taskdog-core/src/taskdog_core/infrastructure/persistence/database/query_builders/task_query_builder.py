"""Query builder for constructing SQLAlchemy SELECT queries for tasks.

This module provides a Fluent Interface for building complex SQL queries
with various filters. It eliminates code duplication between get_filtered()
and count_tasks() methods in SqliteTaskRepository.

The builder supports the hybrid filtering architecture where simple filters
(archived, status, tags, dates) are translated to SQL for optimal performance.
"""

from datetime import date
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.sql.selectable import Select

from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.infrastructure.persistence.database.models import (
    TagModel,
    TaskModel,
    TaskTagModel,
)


class TaskQueryBuilder:
    """Builder for constructing SQLAlchemy SELECT queries with filters.

    This builder follows the Fluent Interface pattern, allowing method chaining
    to progressively add filters to a SELECT statement. It supports all SQL-compatible
    filters used in the hybrid filtering architecture.

    Example:
        >>> builder = TaskQueryBuilder(select(TaskModel))
        >>> stmt = (
        ...     builder
        ...     .with_archived_filter(include_archived=False)
        ...     .with_status_filter(status=TaskStatus.PENDING)
        ...     .with_tag_filter(tags=["urgent"], match_all=False)
        ...     .with_date_filter(start_date=date(2025, 1, 1), end_date=None)
        ...     .build()
        ... )

    Note:
        This builder is designed to work with the existing hybrid filtering
        architecture in TaskQueryService, which separates SQL-compatible filters
        from complex Python-only filters.
    """

    def __init__(self, base_stmt: Select[Any]):
        """Initialize the builder with a base SELECT statement.

        Args:
            base_stmt: Base SQLAlchemy SELECT statement to build upon.
                       Can be select(TaskModel) for entity queries or
                       select(func.count(TaskModel.id)) for count queries.
        """
        self._stmt = base_stmt

    def with_archived_filter(self, include_archived: bool = True) -> "TaskQueryBuilder":
        """Add archived status filter to the query.

        Args:
            include_archived: If False, exclude archived tasks (default: True)

        Returns:
            Self for method chaining

        Note:
            Uses indexed is_archived column for efficient filtering.
        """
        if not include_archived:
            self._stmt = self._stmt.where(TaskModel.is_archived == False)  # noqa: E712

        return self

    def with_status_filter(
        self, status: TaskStatus | None = None
    ) -> "TaskQueryBuilder":
        """Add task status filter to the query.

        Args:
            status: Filter by task status (default: None, no status filter)

        Returns:
            Self for method chaining

        Note:
            Uses indexed status column for efficient filtering.
        """
        if status is not None:
            self._stmt = self._stmt.where(TaskModel.status == status.value)

        return self

    def with_tag_filter(
        self,
        tags: list[str] | None = None,
        match_all: bool = False,
    ) -> "TaskQueryBuilder":
        """Add tag filter to the query.

        Args:
            tags: Filter by tags (default: None, no tag filter)
            match_all: If True, require all tags (AND logic);
                      if False, any tag (OR logic) (default: False)

        Returns:
            Self for method chaining

        Note:
            Uses SQL JOIN with tags and task_tags tables for efficiency.
            AND logic: Creates multiple subqueries (one per tag)
            OR logic: Creates single subquery with IN clause
        """
        if tags:
            if match_all:
                # AND logic: task must have ALL specified tags
                for tag in tags:
                    tag_subquery = (
                        select(TaskTagModel.task_id)
                        .join(TagModel, TaskTagModel.tag_id == TagModel.id)
                        .where(TagModel.name == tag)
                    )
                    self._stmt = self._stmt.where(TaskModel.id.in_(tag_subquery))  # type: ignore[attr-defined]
            else:
                # OR logic: task must have ANY of the specified tags
                tag_subquery = (
                    select(TaskTagModel.task_id)
                    .join(TagModel, TaskTagModel.tag_id == TagModel.id)
                    .where(TagModel.name.in_(tags))  # type: ignore[attr-defined]
                )
                self._stmt = self._stmt.where(TaskModel.id.in_(tag_subquery))  # type: ignore[attr-defined]

        return self

    def with_date_filter(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> "TaskQueryBuilder":
        """Add date range filter to the query.

        This filter checks multiple date fields (deadline, planned_start, planned_end,
        actual_start, actual_end) and matches tasks where ANY of these fields fall
        within the specified range.

        Args:
            start_date: Filter tasks with any date >= start_date (default: None)
            end_date: Filter tasks with any date <= end_date (default: None)

        Returns:
            Self for method chaining

        Note:
            The conditions are combined with OR logic, as we want to match tasks
            where ANY of the date fields fall within the range.
        """
        if start_date is not None or end_date is not None:
            date_conditions = self._build_date_filter_conditions(start_date, end_date)
            if date_conditions:
                self._stmt = self._stmt.where(or_(*date_conditions))

        return self

    def build(self) -> Select[Any]:
        """Build and return the final SELECT statement.

        Returns:
            Configured SQLAlchemy SELECT statement ready for execution

        Note:
            This method returns the statement; it does not execute the query.
            The caller is responsible for executing the statement within
            an appropriate database session.
        """
        return self._stmt

    def _build_date_filter_conditions(
        self, start_date: date | None, end_date: date | None
    ) -> list[ColumnElement[bool]]:
        """Build SQL date filter conditions for multiple date fields.

        This helper method creates SQLAlchemy filter conditions for date range
        filtering across all date fields (deadline, planned_start, planned_end,
        actual_start, actual_end). It handles three cases for each field:
        - Both start and end dates: field.between(start_date, end_date)
        - Only start date: field >= start_date
        - Only end date: field <= end_date

        Args:
            start_date: Minimum date for filtering (inclusive), or None
            end_date: Maximum date for filtering (inclusive), or None

        Returns:
            List of SQLAlchemy filter conditions (empty if both dates are None)

        Note:
            The returned conditions should be combined with OR logic, as we want
            to match tasks where ANY of the date fields fall within the range.
        """
        date_conditions: list[ColumnElement[bool]] = []

        # Define all date fields to check
        date_fields = [
            TaskModel.deadline,
            TaskModel.planned_start,
            TaskModel.planned_end,
            TaskModel.actual_start,
            TaskModel.actual_end,
        ]

        # Build conditions for each date field
        for field in date_fields:
            if start_date and end_date:
                date_conditions.append(field.between(start_date, end_date))  # type: ignore[attr-defined]
            elif start_date:
                date_conditions.append(field >= start_date)  # type: ignore[arg-type]
            elif end_date:
                date_conditions.append(field <= end_date)  # type: ignore[arg-type]

        return date_conditions
