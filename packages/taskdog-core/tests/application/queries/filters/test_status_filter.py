"""Tests for StatusFilter."""

import unittest

from taskdog_core.application.queries.filters.status_filter import StatusFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestStatusFilter(unittest.TestCase):
    """Test cases for StatusFilter."""

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
        self.tasks = [
            self.task_pending,
            self.task_in_progress,
            self.task_completed,
            self.task_canceled,
        ]

    def test_filter_by_each_status(self):
        """Test filter returns only tasks matching each status."""
        # Test data: (status, expected_id, expected_status)
        test_cases = [
            (TaskStatus.PENDING, 1, TaskStatus.PENDING),
            (TaskStatus.IN_PROGRESS, 2, TaskStatus.IN_PROGRESS),
            (TaskStatus.COMPLETED, 3, TaskStatus.COMPLETED),
            (TaskStatus.CANCELED, 4, TaskStatus.CANCELED),
        ]

        for status, expected_id, expected_status in test_cases:
            with self.subTest(status=status.name):
                status_filter = StatusFilter(status)
                result = status_filter.filter(self.tasks)

                self.assertEqual(len(result), 1)
                self.assertEqual(result[0].id, expected_id)
                self.assertEqual(result[0].status, expected_status)

    def test_filter_with_multiple_matching_tasks(self):
        """Test filter with multiple tasks of same status."""
        task_pending_2 = Task(
            id=5, name="Pending 2", status=TaskStatus.PENDING, priority=2
        )
        tasks = [self.task_pending, self.task_in_progress, task_pending_2]

        status_filter = StatusFilter(TaskStatus.PENDING)
        result = status_filter.filter(tasks)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 5)

    def test_filter_with_no_matching_tasks(self):
        """Test filter with no tasks matching the status."""
        # Only IN_PROGRESS tasks
        tasks = [self.task_in_progress]

        status_filter = StatusFilter(TaskStatus.PENDING)
        result = status_filter.filter(tasks)

        self.assertEqual(len(result), 0)

    def test_filter_with_empty_list(self):
        """Test filter with empty task list."""
        status_filter = StatusFilter(TaskStatus.PENDING)
        result = status_filter.filter([])

        self.assertEqual(len(result), 0)

    def test_filter_stores_status(self):
        """Test that filter stores the target status."""
        status_filter = StatusFilter(TaskStatus.COMPLETED)

        self.assertEqual(status_filter.status, TaskStatus.COMPLETED)


if __name__ == "__main__":
    unittest.main()
