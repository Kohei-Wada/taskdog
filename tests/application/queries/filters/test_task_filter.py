"""Tests for TaskFilter base class."""

import unittest

from application.queries.filters.task_filter import TaskFilter
from domain.entities.task import Task


class ConcreteFilter(TaskFilter):
    """Concrete implementation of TaskFilter for testing."""

    def filter(self, tasks: list[Task]) -> list[Task]:
        """Return all tasks."""
        return tasks


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


if __name__ == "__main__":
    unittest.main()
