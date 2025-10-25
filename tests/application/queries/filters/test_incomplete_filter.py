"""Tests for IncompleteFilter."""

import unittest

from application.queries.filters.incomplete_filter import IncompleteFilter
from domain.entities.task import Task, TaskStatus


class TestIncompleteFilter(unittest.TestCase):
    """Test cases for IncompleteFilter."""

    def setUp(self):
        """Create sample tasks for testing."""
        self.task_pending = Task(id=1, name="Pending", status=TaskStatus.PENDING, priority=1)
        self.task_in_progress = Task(
            id=2, name="In Progress", status=TaskStatus.IN_PROGRESS, priority=1
        )
        self.task_completed = Task(id=3, name="Completed", status=TaskStatus.COMPLETED, priority=1)
        self.task_canceled = Task(id=4, name="Canceled", status=TaskStatus.CANCELED, priority=1)

    def test_filter_by_completion_status(self):
        """Test filter includes incomplete and excludes complete tasks."""
        incomplete_filter = IncompleteFilter()

        # Test data: (status, should_include)
        test_cases = [
            (TaskStatus.PENDING, True),
            (TaskStatus.IN_PROGRESS, True),
            (TaskStatus.COMPLETED, False),
            (TaskStatus.CANCELED, False),
        ]

        task_map = {
            TaskStatus.PENDING: self.task_pending,
            TaskStatus.IN_PROGRESS: self.task_in_progress,
            TaskStatus.COMPLETED: self.task_completed,
            TaskStatus.CANCELED: self.task_canceled,
        }

        for status, should_include in test_cases:
            with self.subTest(status=status, should_include=should_include):
                tasks = [task_map[status]]
                result = incomplete_filter.filter(tasks)

                if should_include:
                    self.assertEqual(len(result), 1)
                    self.assertEqual(result[0].status, status)
                else:
                    self.assertEqual(len(result), 0)

    def test_filter_with_mixed_statuses(self):
        """Test filter with mix of complete and incomplete tasks."""
        incomplete_filter = IncompleteFilter()
        tasks = [
            self.task_pending,
            self.task_in_progress,
            self.task_completed,
            self.task_canceled,
        ]

        result = incomplete_filter.filter(tasks)

        self.assertEqual(len(result), 2)
        self.assertIn(self.task_pending, result)
        self.assertIn(self.task_in_progress, result)

    def test_filter_with_empty_list(self):
        """Test filter with empty task list."""
        incomplete_filter = IncompleteFilter()
        result = incomplete_filter.filter([])

        self.assertEqual(len(result), 0)

    def test_filter_uses_is_finished_property(self):
        """Test filter correctly uses Task.is_finished property."""
        incomplete_filter = IncompleteFilter()

        # is_finished should be False for PENDING and IN_PROGRESS
        self.assertFalse(self.task_pending.is_finished)
        self.assertFalse(self.task_in_progress.is_finished)

        # is_finished should be True for COMPLETED and CANCELED
        self.assertTrue(self.task_completed.is_finished)
        self.assertTrue(self.task_canceled.is_finished)

        # Filter should only include not is_finished
        tasks = [
            self.task_pending,
            self.task_in_progress,
            self.task_completed,
            self.task_canceled,
        ]
        result = incomplete_filter.filter(tasks)

        for task in result:
            self.assertFalse(task.is_finished)


if __name__ == "__main__":
    unittest.main()
