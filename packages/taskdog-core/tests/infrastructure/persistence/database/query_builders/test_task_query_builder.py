"""Unit tests for TaskQueryBuilder.

This module tests the TaskQueryBuilder class, which provides a Fluent Interface
for building SQLAlchemy SELECT queries with various filters.

The tests verify:
1. Individual filter methods add correct WHERE clauses
2. Method chaining works correctly (Fluent Interface)
3. Multiple filters can be combined
4. Edge cases (empty tags, None values, etc.) are handled correctly
5. Generated SQL matches expected patterns
"""

from datetime import date

from sqlalchemy import func, select

from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.infrastructure.persistence.database.models import TaskModel
from taskdog_core.infrastructure.persistence.database.query_builders import (
    TaskQueryBuilder,
)


class TestTaskQueryBuilder:
    """Test cases for TaskQueryBuilder."""

    def test_build_returns_base_statement_when_no_filters_applied(self):
        """Test that build() returns the base statement when no filters are added."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.build()

        # The result should be the same as the base statement
        assert str(result) == str(base_stmt)

    def test_with_archived_filter_includes_all_when_true(self):
        """Test that with_archived_filter(True) doesn't add WHERE clause."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_archived_filter(include_archived=True).build()

        # Should not add any WHERE clause
        assert str(result) == str(base_stmt)

    def test_with_archived_filter_excludes_archived_when_false(self):
        """Test that with_archived_filter(False) adds is_archived = false clause."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_archived_filter(include_archived=False).build()

        # Should add WHERE clause for is_archived
        result_str = str(result).lower()
        assert "where" in result_str
        assert "is_archived" in result_str

    def test_with_status_filter_no_filter_when_none(self):
        """Test that with_status_filter(None) doesn't add WHERE clause."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_status_filter(status=None).build()

        # Should not add any WHERE clause
        assert str(result) == str(base_stmt)

    def test_with_status_filter_adds_status_clause(self):
        """Test that with_status_filter adds correct WHERE clause for status."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_status_filter(status=TaskStatus.PENDING).build()

        # Should add WHERE clause for status
        result_str = str(result).lower()
        assert "where" in result_str
        assert "status" in result_str

    def test_with_tag_filter_no_filter_when_none(self):
        """Test that with_tag_filter(None) doesn't add WHERE clause."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_tag_filter(tags=None).build()

        # Should not add any WHERE clause
        assert str(result) == str(base_stmt)

    def test_with_tag_filter_no_filter_when_empty_list(self):
        """Test that with_tag_filter([]) doesn't add WHERE clause."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_tag_filter(tags=[]).build()

        # Should not add any WHERE clause
        assert str(result) == str(base_stmt)

    def test_with_tag_filter_or_logic(self):
        """Test that with_tag_filter adds OR logic for multiple tags."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_tag_filter(
            tags=["urgent", "important"], match_all=False
        ).build()

        # Should add WHERE clause with subquery
        result_str = str(result).lower()
        assert "where" in result_str
        assert "in" in result_str
        # Should use tags.name IN (...) for OR logic
        assert "tags.name in" in result_str

    def test_with_tag_filter_and_logic(self):
        """Test that with_tag_filter adds AND logic when match_all=True."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_tag_filter(
            tags=["urgent", "important"], match_all=True
        ).build()

        # Should add multiple WHERE clauses (one per tag)
        result_str = str(result).lower()
        assert "where" in result_str
        # AND logic creates multiple subqueries
        # Count occurrences of subquery pattern
        subquery_count = result_str.count("task_tags.task_id")
        assert subquery_count >= 2

    def test_with_date_filter_no_filter_when_both_none(self):
        """Test that with_date_filter(None, None) doesn't add WHERE clause."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_date_filter(start_date=None, end_date=None).build()

        # Should not add any WHERE clause
        assert str(result) == str(base_stmt)

    def test_with_date_filter_start_date_only(self):
        """Test that with_date_filter adds >= clause for start_date."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_date_filter(
            start_date=date(2025, 1, 1), end_date=None
        ).build()

        # Should add WHERE clause with OR conditions for multiple date fields
        result_str = str(result).lower()
        assert "where" in result_str
        # Should check multiple date fields
        assert "deadline" in result_str

    def test_with_date_filter_end_date_only(self):
        """Test that with_date_filter adds <= clause for end_date."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_date_filter(
            start_date=None, end_date=date(2025, 12, 31)
        ).build()

        # Should add WHERE clause with OR conditions for multiple date fields
        result_str = str(result).lower()
        assert "where" in result_str
        assert "deadline" in result_str

    def test_with_date_filter_both_dates(self):
        """Test that with_date_filter adds BETWEEN clause for date range."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_date_filter(
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        ).build()

        # Should add WHERE clause with BETWEEN for date range
        result_str = str(result).lower()
        assert "where" in result_str
        assert "between" in result_str
        assert "deadline" in result_str

    def test_method_chaining_fluent_interface(self):
        """Test that methods can be chained (Fluent Interface pattern)."""
        base_stmt = select(TaskModel)

        # This should not raise any errors
        result = (
            TaskQueryBuilder(base_stmt)
            .with_archived_filter(include_archived=False)
            .with_status_filter(status=TaskStatus.PENDING)
            .with_tag_filter(tags=["urgent"], match_all=False)
            .with_date_filter(start_date=date(2025, 1, 1), end_date=None)
            .build()
        )

        # Should have all filters applied
        result_str = str(result).lower()
        assert "is_archived" in result_str
        assert "status" in result_str
        assert "tags" in result_str
        assert "deadline" in result_str

    def test_multiple_filters_combined(self):
        """Test that multiple filters are correctly combined with AND logic."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = (
            builder.with_archived_filter(include_archived=False)
            .with_status_filter(status=TaskStatus.IN_PROGRESS)
            .build()
        )

        # Should combine filters with AND logic
        result_str = str(result).lower()
        assert "is_archived" in result_str
        assert "status" in result_str
        # Both conditions should be present (implicit AND in SQL WHERE clause)

    def test_works_with_count_query(self):
        """Test that builder works with COUNT queries (not just SELECT)."""
        # Use COUNT statement instead of SELECT
        count_stmt = select(func.count(TaskModel.id))
        builder = TaskQueryBuilder(count_stmt)

        result = (
            builder.with_archived_filter(include_archived=False)
            .with_status_filter(status=TaskStatus.COMPLETED)
            .build()
        )

        # Should work with COUNT and add filters
        result_str = str(result).lower()
        assert "count" in result_str
        assert "is_archived" in result_str
        assert "status" in result_str

    def test_empty_tags_list_handled_correctly(self):
        """Test that empty tags list doesn't cause errors."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        # Should not raise errors
        result = builder.with_tag_filter(tags=[], match_all=False).build()

        # Should not add tag filter
        assert str(result) == str(base_stmt)

    def test_single_tag_or_logic(self):
        """Test that single tag with OR logic works correctly."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_tag_filter(tags=["urgent"], match_all=False).build()

        # Should add WHERE clause with subquery
        result_str = str(result).lower()
        assert "where" in result_str
        assert "tags" in result_str

    def test_single_tag_and_logic(self):
        """Test that single tag with AND logic works correctly."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_tag_filter(tags=["urgent"], match_all=True).build()

        # Should add WHERE clause with subquery
        result_str = str(result).lower()
        assert "where" in result_str
        assert "tags" in result_str

    def test_build_can_be_called_multiple_times(self):
        """Test that build() can be called multiple times without side effects."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt).with_archived_filter(
            include_archived=False
        )

        result1 = builder.build()
        result2 = builder.build()

        # Both results should be identical
        assert str(result1) == str(result2)

    def test_date_filter_checks_all_five_date_fields(self):
        """Test that date filter creates conditions for all five date fields."""
        base_stmt = select(TaskModel)
        builder = TaskQueryBuilder(base_stmt)

        result = builder.with_date_filter(
            start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        ).build()

        result_str = str(result).lower()

        # Should check all five date fields
        assert "deadline" in result_str
        assert "planned_start" in result_str
        assert "planned_end" in result_str
        assert "actual_start" in result_str
        assert "actual_end" in result_str
