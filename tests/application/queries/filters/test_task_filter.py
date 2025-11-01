"""Tests for TaskFilter base class."""

import unittest

from application.queries.filters.composite_filter import CompositeFilter
from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task, TaskStatus


class ConcreteFilter(TaskFilter):
    """Concrete implementation of TaskFilter for testing."""

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Return all tasks."""
        return tasks


class PendingOnlyFilter(TaskFilter):
    """Filter that returns only pending tasks."""

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Return only pending tasks."""
        return [task for task in tasks if task.status == TaskStatus.PENDING]


class HighPriorityFilter(TaskFilter):
    """Filter that returns only high priority tasks (priority >= 5)."""

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Return only high priority tasks."""
        return [task for task in tasks if task.priority >= 5]


class TestTaskFilter(unittest.TestCase):
    """Test cases for TaskFilter abstract base class."""

    def test_task_filter_is_abstract(self):
        """Test TaskFilter cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            TaskFilter()  # type: ignore[abstract]

    def test_concrete_filter_can_be_instantiated(self):
        """Test concrete implementation can be instantiated."""
        concrete_filter = ConcreteFilter()

        self.assertIsInstance(concrete_filter, TaskFilter)

    def test_concrete_filter_has_filter_method(self):
        """Test concrete filter implements filter method."""
        concrete_filter = ConcreteFilter()

        self.assertTrue(hasattr(concrete_filter, "filter"))
        self.assertTrue(callable(concrete_filter.filter))

    def test_filter_method_signature(self):
        """Test filter method has correct signature."""
        concrete_filter = ConcreteFilter()
        tasks = []

        # Should not raise
        result = concrete_filter.filter(tasks)

        self.assertIsInstance(result, list)

    def test_rshift_operator_composes_filters(self):
        """Test >> operator creates a composite filter."""
        filter1 = PendingOnlyFilter()
        filter2 = HighPriorityFilter()

        composed = filter1 >> filter2

        self.assertIsInstance(composed, CompositeFilter)
        self.assertEqual(len(composed.filters), 2)
        self.assertIs(composed.filters[0], filter1)
        self.assertIs(composed.filters[1], filter2)

    def test_rshift_operator_filters_in_sequence(self):
        """Test >> operator applies filters in sequence (AND logic)."""
        task1 = Task(id=1, name="Task 1", status=TaskStatus.PENDING, priority=5)
        task2 = Task(id=2, name="Task 2", status=TaskStatus.PENDING, priority=3)
        task3 = Task(id=3, name="Task 3", status=TaskStatus.COMPLETED, priority=5)
        task4 = Task(id=4, name="Task 4", status=TaskStatus.COMPLETED, priority=1)
        tasks = [task1, task2, task3, task4]

        # Compose: pending AND high priority
        composed = PendingOnlyFilter() >> HighPriorityFilter()
        result = composed.filter(tasks)

        # Should only return task1 (pending AND priority >= 5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_rshift_operator_with_none_returns_self(self):
        """Test >> operator with None returns self."""
        filter1 = PendingOnlyFilter()

        result = filter1 >> None

        self.assertIs(result, filter1)

    def test_rshift_operator_chains_multiple_filters(self):
        """Test >> operator can chain multiple filters."""
        task1 = Task(id=1, name="Task 1", status=TaskStatus.PENDING, priority=5)
        task2 = Task(id=2, name="Task 2", status=TaskStatus.PENDING, priority=3)
        tasks = [task1, task2]

        # Chain three filters
        composed = ConcreteFilter() >> PendingOnlyFilter() >> HighPriorityFilter()
        result = composed.filter(tasks)

        # Should only return task1
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 1)

    def test_rshift_operator_extends_composite_filter(self):
        """Test >> operator extends existing CompositeFilter efficiently."""
        filter1 = PendingOnlyFilter()
        filter2 = HighPriorityFilter()
        filter3 = ConcreteFilter()

        # First composition
        composed1 = filter1 >> filter2
        self.assertEqual(len(composed1.filters), 2)

        # Extend with another filter
        composed2 = composed1 >> filter3
        self.assertEqual(len(composed2.filters), 3)
        self.assertIs(composed2.filters[0], filter1)
        self.assertIs(composed2.filters[1], filter2)
        self.assertIs(composed2.filters[2], filter3)

    def test_rshift_operator_with_composite_on_right(self):
        """Test >> operator when right side is already a CompositeFilter."""
        filter1 = PendingOnlyFilter()
        filter2 = HighPriorityFilter()
        filter3 = ConcreteFilter()

        # Create composite on right
        composite_right = filter2 >> filter3
        self.assertEqual(len(composite_right.filters), 2)

        # Prepend filter1
        result = filter1 >> composite_right
        self.assertEqual(len(result.filters), 3)
        self.assertIs(result.filters[0], filter1)
        self.assertIs(result.filters[1], filter2)
        self.assertIs(result.filters[2], filter3)


if __name__ == "__main__":
    unittest.main()
