"""Tests for filter_helpers module."""

import unittest
from datetime import datetime

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.date_range_filter import DateRangeFilter
from application.queries.filters.non_archived_filter import NonArchivedFilter
from application.queries.filters.status_filter import StatusFilter
from application.queries.filters.tag_filter import TagFilter
from domain.entities.task import TaskStatus
from presentation.cli.commands.filter_helpers import build_task_filter


class TestBuildTaskFilter(unittest.TestCase):
    """Tests for build_task_filter function."""

    def test_default_returns_incomplete_filter(self):
        """Test default (no options) returns NonArchivedFilter."""
        result = build_task_filter(all=False, status=None)

        self.assertIsInstance(result, NonArchivedFilter)

    def test_all_only_returns_none(self):
        """Test --all only returns None (no filter)."""
        result = build_task_filter(all=True, status=None)

        self.assertIsNone(result)

    def test_status_only_returns_composite_filter(self):
        """Test --status only returns CompositeFilter with NonArchivedFilter + StatusFilter."""
        result = build_task_filter(all=False, status="pending")

        self.assertIsInstance(result, CompositeFilter)
        self.assertEqual(len(result.filters), 2)
        self.assertIsInstance(result.filters[0], NonArchivedFilter)
        self.assertIsInstance(result.filters[1], StatusFilter)
        self.assertEqual(result.filters[1].status, TaskStatus.PENDING)

    def test_all_and_status_returns_status_filter_only(self):
        """Test --all --status returns StatusFilter only (no NonArchivedFilter)."""
        result = build_task_filter(all=True, status="canceled")

        self.assertIsInstance(result, StatusFilter)
        self.assertEqual(result.status, TaskStatus.CANCELED)

    def test_status_case_insensitive(self):
        """Test status parameter is case-insensitive."""
        result_lower = build_task_filter(all=True, status="completed")
        result_upper = build_task_filter(all=True, status="COMPLETED")
        result_mixed = build_task_filter(all=True, status="CoMpLeTeD")

        self.assertEqual(result_lower.status, TaskStatus.COMPLETED)
        self.assertEqual(result_upper.status, TaskStatus.COMPLETED)
        self.assertEqual(result_mixed.status, TaskStatus.COMPLETED)

    def test_all_statuses_supported(self):
        """Test all TaskStatus enum values are supported."""
        for status in ["pending", "in_progress", "completed", "canceled"]:
            result = build_task_filter(all=True, status=status)
            self.assertIsInstance(result, StatusFilter)

            expected_status = TaskStatus(status.upper())
            self.assertEqual(result.status, expected_status)

    def test_tags_only_returns_composite_filter(self):
        """Test tags only returns CompositeFilter with NonArchivedFilter + TagFilter."""
        result = build_task_filter(all=False, status=None, tags=["work", "urgent"])

        self.assertIsInstance(result, CompositeFilter)
        self.assertEqual(len(result.filters), 2)
        self.assertIsInstance(result.filters[0], NonArchivedFilter)
        self.assertIsInstance(result.filters[1], TagFilter)
        self.assertEqual(result.filters[1].tags, ["work", "urgent"])
        self.assertFalse(result.filters[1].match_all)

    def test_tags_with_match_all(self):
        """Test tags with match_all=True creates TagFilter with AND logic."""
        result = build_task_filter(all=False, status=None, tags=["work"], match_all=True)

        self.assertIsInstance(result, CompositeFilter)
        tag_filter = result.filters[1]
        self.assertIsInstance(tag_filter, TagFilter)
        self.assertTrue(tag_filter.match_all)

    def test_status_and_tags_returns_composite_filter(self):
        """Test status + tags returns CompositeFilter with all filters."""
        result = build_task_filter(all=False, status="pending", tags=["work"])

        self.assertIsInstance(result, CompositeFilter)
        self.assertEqual(len(result.filters), 3)
        self.assertIsInstance(result.filters[0], NonArchivedFilter)
        self.assertIsInstance(result.filters[1], StatusFilter)
        self.assertIsInstance(result.filters[2], TagFilter)

    def test_all_status_and_tags(self):
        """Test --all with status and tags excludes NonArchivedFilter."""
        result = build_task_filter(all=True, status="completed", tags=["work"])

        self.assertIsInstance(result, CompositeFilter)
        self.assertEqual(len(result.filters), 2)
        self.assertIsInstance(result.filters[0], StatusFilter)
        self.assertIsInstance(result.filters[1], TagFilter)

    def test_date_range_only_returns_composite_filter(self):
        """Test date range only returns CompositeFilter with NonArchivedFilter + DateRangeFilter."""
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 31)
        result = build_task_filter(all=False, status=None, start_date=start_date, end_date=end_date)

        self.assertIsInstance(result, CompositeFilter)
        self.assertEqual(len(result.filters), 2)
        self.assertIsInstance(result.filters[0], NonArchivedFilter)
        self.assertIsInstance(result.filters[1], DateRangeFilter)

    def test_all_filters_combined(self):
        """Test all filter options combined creates CompositeFilter with all filters."""
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 10, 31)
        result = build_task_filter(
            all=False,
            status="pending",
            tags=["work", "urgent"],
            match_all=True,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertIsInstance(result, CompositeFilter)
        self.assertEqual(len(result.filters), 4)
        self.assertIsInstance(result.filters[0], NonArchivedFilter)
        self.assertIsInstance(result.filters[1], StatusFilter)
        self.assertIsInstance(result.filters[2], TagFilter)
        self.assertIsInstance(result.filters[3], DateRangeFilter)

    def test_empty_tags_list_ignored(self):
        """Test empty tags list is ignored (no TagFilter added)."""
        result = build_task_filter(all=False, status=None, tags=[])

        # Should only have NonArchivedFilter, no TagFilter
        self.assertIsInstance(result, NonArchivedFilter)

    def test_none_tags_ignored(self):
        """Test None tags is ignored (no TagFilter added)."""
        result = build_task_filter(all=False, status=None, tags=None)

        # Should only have NonArchivedFilter, no TagFilter
        self.assertIsInstance(result, NonArchivedFilter)

    def test_single_filter_not_wrapped_in_composite(self):
        """Test single filter is returned directly, not wrapped in CompositeFilter."""
        # Only NonArchivedFilter
        result = build_task_filter(all=False, status=None)
        self.assertIsInstance(result, NonArchivedFilter)
        self.assertNotIsInstance(result, CompositeFilter)

        # Only StatusFilter (with --all)
        result = build_task_filter(all=True, status="pending")
        self.assertIsInstance(result, StatusFilter)
        self.assertNotIsInstance(result, CompositeFilter)


if __name__ == "__main__":
    unittest.main()
