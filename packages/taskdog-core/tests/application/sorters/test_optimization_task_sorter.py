"""Unit tests for OptimizationTaskSorter service."""

import unittest
from datetime import datetime

from taskdog_core.application.sorters.optimization_task_sorter import (
    OptimizationTaskSorter,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestOptimizationTaskSorter(unittest.TestCase):
    """Test cases for OptimizationTaskSorter."""

    def setUp(self):
        """Set up test fixtures."""
        self.start_date = datetime(2025, 1, 6, 9, 0, 0)  # Monday 9:00 AM
        self.sorter = OptimizationTaskSorter(self.start_date)

    def test_sort_by_priority_field(self):
        """Test that tasks are sorted by priority field."""
        tasks = [
            Task(id=1, name="Low priority", priority=50, status=TaskStatus.PENDING),
            Task(id=2, name="High priority", priority=200, status=TaskStatus.PENDING),
            Task(id=3, name="Medium priority", priority=100, status=TaskStatus.PENDING),
        ]

        result = self.sorter.sort_by_priority(tasks)

        # Higher priority should come first
        self.assertEqual(result[0].id, 2)  # Priority 200
        self.assertEqual(result[1].id, 3)  # Priority 100
        self.assertEqual(result[2].id, 1)  # Priority 50

    def test_sort_by_deadline_urgency(self):
        """Test that tasks with closer deadlines are prioritized."""
        tasks = [
            Task(
                id=1,
                name="Task with distant deadline",
                priority=100,
                status=TaskStatus.PENDING,
                deadline=datetime(2025, 1, 20, 18, 0, 0),  # 14 days away
            ),
            Task(
                id=2,
                name="Task with close deadline",
                priority=100,
                status=TaskStatus.PENDING,
                deadline=datetime(2025, 1, 8, 18, 0, 0),  # 2 days away
            ),
            Task(
                id=3,
                name="Task without deadline",
                priority=100,
                status=TaskStatus.PENDING,
                deadline=None,
            ),
        ]

        result = self.sorter.sort_by_priority(tasks)

        # Closer deadline should come first
        self.assertEqual(result[0].id, 2)  # 2 days away
        self.assertEqual(result[1].id, 1)  # 14 days away
        self.assertEqual(result[2].id, 3)  # No deadline (infinity)

    def test_sort_by_combined_criteria(self):
        """Test sorting with multiple criteria combined."""
        tasks = [
            Task(
                id=1,
                name="Low priority, distant deadline",
                priority=50,
                status=TaskStatus.PENDING,
                deadline=datetime(2025, 1, 20, 18, 0, 0),
            ),
            Task(
                id=2,
                name="High priority, close deadline",
                priority=200,
                status=TaskStatus.PENDING,
                deadline=datetime(2025, 1, 8, 18, 0, 0),
            ),
            Task(
                id=3,
                name="Medium priority, medium deadline",
                priority=100,
                status=TaskStatus.PENDING,
                deadline=datetime(2025, 1, 15, 18, 0, 0),
            ),
        ]

        result = self.sorter.sort_by_priority(tasks)

        # Deadline first, then priority
        self.assertEqual(result[0].id, 2)  # Close deadline (2 days)
        self.assertEqual(result[1].id, 3)  # Medium deadline (9 days)
        self.assertEqual(result[2].id, 1)  # Distant deadline (14 days)

    def test_sort_stable_with_task_id(self):
        """Test that tasks with identical criteria are sorted by task ID."""
        tasks = [
            Task(id=3, name="Task 3", priority=100, status=TaskStatus.PENDING),
            Task(id=1, name="Task 1", priority=100, status=TaskStatus.PENDING),
            Task(id=2, name="Task 2", priority=100, status=TaskStatus.PENDING),
        ]

        result = self.sorter.sort_by_priority(tasks)

        # Should be sorted by ID
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[2].id, 3)

    def test_sort_empty_list(self):
        """Test sorting empty list returns empty list."""
        result = self.sorter.sort_by_priority([])
        self.assertEqual(result, [])

    def test_sort_single_task(self):
        """Test sorting single task returns same task."""
        tasks = [
            Task(id=1, name="Single task", priority=100, status=TaskStatus.PENDING)
        ]

        result = self.sorter.sort_by_priority(tasks)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)


if __name__ == "__main__":
    unittest.main()
