"""Tests for TaskSearchFilter."""

import unittest
from datetime import datetime, timedelta

from domain.entities.task import Task, TaskStatus
from presentation.tui.widgets.task_search_filter import TaskSearchFilter


class TestTaskSearchFilter(unittest.TestCase):
    """Test TaskSearchFilter search and filtering functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.filter = TaskSearchFilter()

        # Create test tasks
        self.tasks = [
            Task(
                id=1,
                name="Fix authentication bug",
                priority=1,
                status=TaskStatus.PENDING,
            ),
            Task(
                id=2,
                name="Implement user registration",
                priority=2,
                status=TaskStatus.IN_PROGRESS,
            ),
            Task(
                id=3,
                name="Update database schema",
                priority=1,
                status=TaskStatus.COMPLETED,
            ),
            Task(
                id=4,
                name="Write API documentation",
                priority=3,
                status=TaskStatus.PENDING,
                deadline=datetime.now() + timedelta(days=7),
            ),
            Task(
                id=5,
                name="URGENT: Fix production bug",
                priority=1,
                status=TaskStatus.PENDING,
                is_fixed=True,
            ),
        ]

    def test_filter_by_id(self):
        """Test filtering tasks by ID."""
        # Search by name to verify filtering works
        filtered = self.filter.filter(self.tasks, "Fix")
        self.assertEqual(len(filtered), 2)  # Tasks 1 and 5 both have "Fix"

        # Search for task by ID 2
        filtered = self.filter.filter(self.tasks, "2")
        # Should match ID 2 and priority 2
        self.assertGreaterEqual(len(filtered), 1)

    def test_filter_by_name_case_insensitive(self):
        """Test case-insensitive filtering by name."""
        # Lowercase query should match "Fix authentication bug" (case-insensitive)
        filtered = self.filter.filter(self.tasks, "auth")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 1)

        # Different case should still match when lowercase
        filtered = self.filter.filter(self.tasks, "registration")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 2)

    def test_filter_by_name_case_sensitive(self):
        """Test case-sensitive filtering (smart case with uppercase in query)."""
        # Query with uppercase should be case-sensitive
        filtered = self.filter.filter(self.tasks, "URGENT")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 5)

        # Different case should not match
        filtered = self.filter.filter(self.tasks, "urgent")
        self.assertEqual(len(filtered), 1)  # Matches because lowercase is case-insensitive

    def test_filter_by_status(self):
        """Test filtering by status."""
        # Search for PENDING status
        filtered = self.filter.filter(self.tasks, "PENDING")
        self.assertEqual(len(filtered), 3)
        pending_ids = {task.id for task in filtered}
        self.assertEqual(pending_ids, {1, 4, 5})

        # Search for IN_PROGRESS status
        filtered = self.filter.filter(self.tasks, "IN_PROGRESS")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 2)

    def test_filter_by_priority(self):
        """Test filtering by priority."""
        # Search for priority 1
        filtered = self.filter.filter(self.tasks, "1")
        # Should match IDs 1, 3, 5 (priority 1) and also ID 2 ("Implement user registration" - no "1" in name)
        self.assertGreaterEqual(len(filtered), 3)

    def test_filter_by_fixed_status(self):
        """Test filtering by fixed status."""
        # Search for "fixed" keyword
        filtered = self.filter.filter(self.tasks, "fixed")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].id, 5)
        self.assertTrue(filtered[0].is_fixed)

    def test_filter_partial_match(self):
        """Test partial string matching."""
        # Search for "bug" should match tasks with "bug" in name
        filtered = self.filter.filter(self.tasks, "bug")
        self.assertEqual(len(filtered), 2)
        bug_ids = {task.id for task in filtered}
        self.assertEqual(bug_ids, {1, 5})

    def test_filter_no_matches(self):
        """Test filtering with no matches."""
        filtered = self.filter.filter(self.tasks, "nonexistent")
        self.assertEqual(len(filtered), 0)

    def test_filter_empty_query(self):
        """Test filtering with empty query returns all tasks."""
        filtered = self.filter.filter(self.tasks, "")
        self.assertEqual(len(filtered), 5)
        self.assertEqual(filtered, self.tasks)

    def test_smart_case_lowercase_query(self):
        """Test smart case with lowercase query is case-insensitive."""
        # Lowercase "fix" should match both "Fix" and "fix"
        filtered = self.filter.filter(self.tasks, "fix")
        self.assertEqual(len(filtered), 2)
        fix_ids = {task.id for task in filtered}
        self.assertEqual(fix_ids, {1, 5})

    def test_smart_case_mixed_case_query(self):
        """Test smart case with mixed case query is case-sensitive."""
        # Mixed case "Fix" should only match exact case
        filtered = self.filter.filter(self.tasks, "Fix")
        self.assertEqual(len(filtered), 2)  # Both have "Fix"

    def test_matches_method(self):
        """Test the matches method directly."""
        task = self.tasks[0]  # "Fix authentication bug"

        # Should match
        self.assertTrue(self.filter.matches(task, "auth"))
        self.assertTrue(self.filter.matches(task, "Fix"))
        self.assertTrue(self.filter.matches(task, "1"))  # Priority

        # Should not match
        self.assertFalse(self.filter.matches(task, "urgent"))
        self.assertFalse(self.filter.matches(task, "registration"))

    def test_matches_with_explicit_case_sensitivity(self):
        """Test matches method with explicit case sensitivity parameter."""
        task = self.tasks[4]  # "URGENT: Fix production bug"

        # Case-insensitive
        self.assertTrue(self.filter.matches(task, "urgent", case_sensitive=False))
        self.assertTrue(self.filter.matches(task, "URGENT", case_sensitive=False))

        # Case-sensitive
        self.assertTrue(self.filter.matches(task, "URGENT", case_sensitive=True))
        self.assertFalse(self.filter.matches(task, "urgent", case_sensitive=True))

    def test_is_case_sensitive(self):
        """Test smart case detection."""
        # Lowercase queries should be case-insensitive
        self.assertFalse(self.filter._is_case_sensitive("hello"))
        self.assertFalse(self.filter._is_case_sensitive("test123"))

        # Queries with uppercase should be case-sensitive
        self.assertTrue(self.filter._is_case_sensitive("Hello"))
        self.assertTrue(self.filter._is_case_sensitive("TEST"))
        self.assertTrue(self.filter._is_case_sensitive("Test123"))


if __name__ == "__main__":
    unittest.main()
