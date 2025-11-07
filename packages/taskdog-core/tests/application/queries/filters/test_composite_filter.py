"""Tests for CompositeFilter."""

import unittest

from taskdog_core.application.queries.filters.composite_filter import CompositeFilter
from taskdog_core.application.queries.filters.status_filter import StatusFilter
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class MockAlwaysTrueFilter(TaskFilter):
    """Mock filter that always returns all tasks."""

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Return all tasks."""
        return tasks


class MockAlwaysFalseFilter(TaskFilter):
    """Mock filter that always returns no tasks."""

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Return no tasks."""
        return []


class TestCompositeFilter(unittest.TestCase):
    """Test cases for CompositeFilter."""

    def setUp(self):
        """Create sample tasks for testing."""
        self.task1 = Task(id=1, name="Task 1", status=TaskStatus.PENDING, priority=1)
        self.task2 = Task(
            id=2, name="Task 2", status=TaskStatus.IN_PROGRESS, priority=2
        )
        self.task3 = Task(id=3, name="Task 3", status=TaskStatus.COMPLETED, priority=3)
        self.task4 = Task(id=4, name="Task 4", status=TaskStatus.CANCELED, priority=1)
        self.tasks = [self.task1, self.task2, self.task3, self.task4]

    def test_filter_with_empty_filter_list_returns_all_tasks(self):
        """Test composite filter with no filters returns all tasks."""
        composite = CompositeFilter([])
        result = composite.filter(self.tasks)

        self.assertEqual(len(result), 4)
        self.assertEqual(result, self.tasks)

    def test_filter_with_single_filter(self):
        """Test composite filter with single filter applies that filter."""
        status_filter = StatusFilter(TaskStatus.PENDING)
        composite = CompositeFilter([status_filter])

        result = composite.filter(self.tasks)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_filter_with_multiple_filters_applies_and_logic(self):
        """Test composite filter applies multiple filters with AND logic."""
        # Filter for PENDING tasks
        pending_filter = StatusFilter(TaskStatus.PENDING)
        # Then filter with always-true (should keep PENDING tasks)
        true_filter = MockAlwaysTrueFilter()

        composite = CompositeFilter([pending_filter, true_filter])
        result = composite.filter(self.tasks)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_filter_with_contradictory_filters_returns_empty(self):
        """Test composite filter with contradictory filters returns empty list."""
        # Filter for PENDING tasks
        pending_filter = StatusFilter(TaskStatus.PENDING)
        # Then filter with always-false
        false_filter = MockAlwaysFalseFilter()

        composite = CompositeFilter([pending_filter, false_filter])
        result = composite.filter(self.tasks)

        self.assertEqual(len(result), 0)

    def test_filter_applies_filters_in_sequence(self):
        """Test that filters are applied in the order they are provided."""
        # First filter: get PENDING tasks (task1)
        pending_filter = StatusFilter(TaskStatus.PENDING)
        # Second filter: get IN_PROGRESS tasks (should find none from task1)
        in_progress_filter = StatusFilter(TaskStatus.IN_PROGRESS)

        composite = CompositeFilter([pending_filter, in_progress_filter])
        result = composite.filter(self.tasks)

        # Should be empty because task1 is PENDING, not IN_PROGRESS
        self.assertEqual(len(result), 0)

    def test_filter_with_three_filters(self):
        """Test composite filter with three filters."""
        # All filters return all tasks
        filter1 = MockAlwaysTrueFilter()
        filter2 = MockAlwaysTrueFilter()
        filter3 = MockAlwaysTrueFilter()

        composite = CompositeFilter([filter1, filter2, filter3])
        result = composite.filter(self.tasks)

        self.assertEqual(len(result), 4)

    def test_filter_with_narrowing_filters(self):
        """Test composite filter that narrows down results progressively."""
        # Create more specific task set
        task_a = Task(id=10, name="A", status=TaskStatus.PENDING, priority=1)
        task_b = Task(id=11, name="B", status=TaskStatus.PENDING, priority=2)
        task_c = Task(id=12, name="C", status=TaskStatus.COMPLETED, priority=1)
        tasks = [task_a, task_b, task_c]

        # First filter: PENDING only
        pending_filter = StatusFilter(TaskStatus.PENDING)
        # Second filter: return only tasks with priority 1
        true_filter = MockAlwaysTrueFilter()

        composite = CompositeFilter([pending_filter, true_filter])
        result = composite.filter(tasks)

        # Should have 2 PENDING tasks
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, 10)
        self.assertEqual(result[1].id, 11)

    def test_filter_with_empty_task_list(self):
        """Test composite filter with empty task list."""
        composite = CompositeFilter([StatusFilter(TaskStatus.PENDING)])
        result = composite.filter([])

        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main()
