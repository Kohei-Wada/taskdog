"""Tests for TaskFilter base class."""

import unittest

from parameterized import parameterized

from taskdog_core.application.queries.filters.composite_filter import CompositeFilter
from taskdog_core.application.queries.filters.task_filter import TaskFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


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

    @parameterized.expand(
        [
            (
                "two_filters_sequence",
                lambda: PendingOnlyFilter() >> HighPriorityFilter(),
                lambda: [
                    Task(id=1, name="Task 1", status=TaskStatus.PENDING, priority=5),
                    Task(id=2, name="Task 2", status=TaskStatus.PENDING, priority=3),
                    Task(id=3, name="Task 3", status=TaskStatus.COMPLETED, priority=5),
                    Task(id=4, name="Task 4", status=TaskStatus.COMPLETED, priority=1),
                ],
                1,
                1,
            ),
            (
                "three_filters_chain",
                lambda: ConcreteFilter() >> PendingOnlyFilter() >> HighPriorityFilter(),
                lambda: [
                    Task(id=1, name="Task 1", status=TaskStatus.PENDING, priority=5),
                    Task(id=2, name="Task 2", status=TaskStatus.PENDING, priority=3),
                ],
                1,
                1,
            ),
        ]
    )
    def test_rshift_operator_filter_execution(
        self, scenario, composed_factory, tasks_factory, expected_count, expected_id
    ):
        """Test >> operator applies filters in sequence."""
        composed = composed_factory()
        tasks = tasks_factory()
        result = composed.filter(tasks)

        self.assertEqual(len(result), expected_count)
        self.assertEqual(result[0].id, expected_id)

    def test_rshift_operator_with_none_returns_self(self):
        """Test >> operator with None returns self."""
        filter1 = PendingOnlyFilter()

        result = filter1 >> None

        self.assertIs(result, filter1)

    @parameterized.expand(
        [
            (
                "extend_composite",
                lambda: (PendingOnlyFilter() >> HighPriorityFilter())
                >> ConcreteFilter(),
                3,
            ),
            (
                "composite_on_right",
                lambda: PendingOnlyFilter()
                >> (HighPriorityFilter() >> ConcreteFilter()),
                3,
            ),
        ]
    )
    def test_rshift_operator_composite_composition(
        self, scenario, composed_factory, expected_filter_count
    ):
        """Test >> operator composition with CompositeFilters."""
        composed = composed_factory()

        self.assertIsInstance(composed, CompositeFilter)
        self.assertEqual(len(composed.filters), expected_filter_count)


if __name__ == "__main__":
    unittest.main()
