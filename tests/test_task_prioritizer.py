"""Unit tests for TaskPrioritizer service."""

import unittest
from datetime import datetime
from unittest.mock import Mock

from application.services.task_prioritizer import TaskPrioritizer
from domain.entities.task import Task, TaskStatus


class TestTaskPrioritizer(unittest.TestCase):
    """Test cases for TaskPrioritizer."""

    def setUp(self):
        """Set up test fixtures."""
        self.start_date = datetime(2025, 1, 6, 9, 0, 0)  # Monday 9:00 AM
        self.mock_repository = Mock()
        self.prioritizer = TaskPrioritizer(self.start_date, self.mock_repository)

    def test_sort_by_priority_field(self):
        """Test that tasks are sorted by priority field."""
        tasks = [
            Task(id=1, name="Low priority", priority=50, status=TaskStatus.PENDING),
            Task(id=2, name="High priority", priority=200, status=TaskStatus.PENDING),
            Task(id=3, name="Medium priority", priority=100, status=TaskStatus.PENDING),
        ]
        # Mock repository to return no children for all tasks
        self.mock_repository.get_children.return_value = []

        result = self.prioritizer.sort_by_priority(tasks)

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
                deadline="2025-01-20 18:00:00",  # 14 days away
            ),
            Task(
                id=2,
                name="Task with close deadline",
                priority=100,
                status=TaskStatus.PENDING,
                deadline="2025-01-08 18:00:00",  # 2 days away
            ),
            Task(
                id=3,
                name="Task without deadline",
                priority=100,
                status=TaskStatus.PENDING,
                deadline=None,
            ),
        ]
        self.mock_repository.get_children.return_value = []

        result = self.prioritizer.sort_by_priority(tasks)

        # Closer deadline should come first
        self.assertEqual(result[0].id, 2)  # 2 days away
        self.assertEqual(result[1].id, 1)  # 14 days away
        self.assertEqual(result[2].id, 3)  # No deadline (infinity)

    def test_sort_by_hierarchy_leaf_before_parent(self):
        """Test that leaf tasks are prioritized before parent tasks."""
        tasks = [
            Task(id=1, name="Parent task", priority=100, status=TaskStatus.PENDING),
            Task(
                id=2,
                name="Child task",
                priority=100,
                status=TaskStatus.PENDING,
                parent_id=1,
            ),
        ]

        # Mock repository to return children for task 1
        def get_children_side_effect(task_id):
            if task_id == 1:
                return [tasks[1]]  # Task 1 has children
            return []

        self.mock_repository.get_children.side_effect = get_children_side_effect

        result = self.prioritizer.sort_by_priority(tasks)

        # Child (leaf) should come before parent
        self.assertEqual(result[0].id, 2)  # Child
        self.assertEqual(result[1].id, 1)  # Parent

    def test_sort_by_combined_criteria(self):
        """Test sorting with multiple criteria combined."""
        tasks = [
            Task(
                id=1,
                name="Low priority, distant deadline",
                priority=50,
                status=TaskStatus.PENDING,
                deadline="2025-01-20 18:00:00",
            ),
            Task(
                id=2,
                name="High priority, close deadline",
                priority=200,
                status=TaskStatus.PENDING,
                deadline="2025-01-08 18:00:00",
            ),
            Task(
                id=3,
                name="Medium priority, medium deadline",
                priority=100,
                status=TaskStatus.PENDING,
                deadline="2025-01-15 18:00:00",
            ),
        ]
        self.mock_repository.get_children.return_value = []

        result = self.prioritizer.sort_by_priority(tasks)

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
        self.mock_repository.get_children.return_value = []

        result = self.prioritizer.sort_by_priority(tasks)

        # Should be sorted by ID
        self.assertEqual(result[0].id, 1)
        self.assertEqual(result[1].id, 2)
        self.assertEqual(result[2].id, 3)

    def test_sort_empty_list(self):
        """Test sorting empty list returns empty list."""
        result = self.prioritizer.sort_by_priority([])
        self.assertEqual(result, [])

    def test_sort_single_task(self):
        """Test sorting single task returns same task."""
        tasks = [Task(id=1, name="Single task", priority=100, status=TaskStatus.PENDING)]
        self.mock_repository.get_children.return_value = []

        result = self.prioritizer.sort_by_priority(tasks)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)


if __name__ == "__main__":
    unittest.main()
