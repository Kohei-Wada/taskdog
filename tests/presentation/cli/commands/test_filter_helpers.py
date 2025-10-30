"""Tests for filter_helpers module."""

import unittest

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.incomplete_filter import IncompleteFilter
from application.queries.filters.status_filter import StatusFilter
from domain.entities.task import TaskStatus
from presentation.cli.commands.filter_helpers import build_task_filter


class TestBuildTaskFilter(unittest.TestCase):
    """Tests for build_task_filter function."""

    def test_default_returns_incomplete_filter(self):
        """Test default (no options) returns IncompleteFilter."""
        result = build_task_filter(all=False, status=None)

        self.assertIsInstance(result, IncompleteFilter)

    def test_all_only_returns_none(self):
        """Test --all only returns None (no filter)."""
        result = build_task_filter(all=True, status=None)

        self.assertIsNone(result)

    def test_status_only_returns_composite_filter(self):
        """Test --status only returns CompositeFilter with IncompleteFilter + StatusFilter."""
        result = build_task_filter(all=False, status="pending")

        self.assertIsInstance(result, CompositeFilter)
        self.assertEqual(len(result.filters), 2)
        self.assertIsInstance(result.filters[0], IncompleteFilter)
        self.assertIsInstance(result.filters[1], StatusFilter)
        self.assertEqual(result.filters[1].status, TaskStatus.PENDING)

    def test_all_and_status_returns_status_filter_only(self):
        """Test --all --status returns StatusFilter only (no IncompleteFilter)."""
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


if __name__ == "__main__":
    unittest.main()
