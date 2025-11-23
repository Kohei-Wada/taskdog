"""Tests for NonArchivedFilter."""

import unittest

from taskdog_core.application.queries.filters.non_archived_filter import (
    NonArchivedFilter,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestNonArchivedFilter(unittest.TestCase):
    """Test cases for NonArchivedFilter."""

    def setUp(self):
        """Create sample tasks for testing."""
        self.task_pending = Task(
            id=1, name="Pending", status=TaskStatus.PENDING, priority=1
        )
        self.task_in_progress = Task(
            id=2, name="In Progress", status=TaskStatus.IN_PROGRESS, priority=1
        )
        self.task_completed = Task(
            id=3, name="Completed", status=TaskStatus.COMPLETED, priority=1
        )
        self.task_canceled = Task(
            id=4, name="Canceled", status=TaskStatus.CANCELED, priority=1
        )

    def test_filter_includes_each_non_archived_status(self):
        """Test filter includes all non-archived statuses."""
        non_archived_filter = NonArchivedFilter()

        # Test data: statuses that should be included
        non_archived_statuses = [
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
            TaskStatus.CANCELED,
        ]

        task_map = {
            TaskStatus.PENDING: self.task_pending,
            TaskStatus.IN_PROGRESS: self.task_in_progress,
            TaskStatus.COMPLETED: self.task_completed,
            TaskStatus.CANCELED: self.task_canceled,
        }

        for status in non_archived_statuses:
            with self.subTest(status=status.name):
                tasks = [task_map[status]]
                result = non_archived_filter.filter(tasks)

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].status, status)

    def test_filter_includes_all_non_archived_statuses(self):
        """Test filter includes all non-archived tasks."""
        non_archived_filter = NonArchivedFilter()
        tasks = [
            self.task_pending,
            self.task_in_progress,
            self.task_completed,
            self.task_canceled,
        ]

        result = non_archived_filter.filter(tasks)

        self.assertEqual(len(result), 4)

    def test_filter_with_empty_list(self):
        """Test filter with empty task list."""
        non_archived_filter = NonArchivedFilter()
        result = non_archived_filter.filter([])

        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
