"""Tests for CompositeFilter."""

import unittest

from parameterized import parameterized

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

    @parameterized.expand(
        [
            (
                "multiple_filters_and_logic",
                lambda self: [
                    StatusFilter(TaskStatus.PENDING),
                    MockAlwaysTrueFilter(),
                ],
                1,
                1,
            ),
            (
                "contradictory_filters_empty",
                lambda self: [
                    StatusFilter(TaskStatus.PENDING),
                    MockAlwaysFalseFilter(),
                ],
                0,
                None,
            ),
            (
                "sequential_filters_no_match",
                lambda self: [
                    StatusFilter(TaskStatus.PENDING),
                    StatusFilter(TaskStatus.IN_PROGRESS),
                ],
                0,
                None,
            ),
            (
                "three_true_filters_all_tasks",
                lambda self: [
                    MockAlwaysTrueFilter(),
                    MockAlwaysTrueFilter(),
                    MockAlwaysTrueFilter(),
                ],
                4,
                None,
            ),
        ]
    )
    def test_filter_combinations(
        self, scenario, filter_factory, expected_count, expected_first_id
    ):
        """Test composite filter with various filter combinations."""
        filters = filter_factory(self)
        composite = CompositeFilter(filters)
        result = composite.filter(self.tasks)

        self.assertEqual(len(result), expected_count)
        if expected_first_id is not None:
            self.assertEqual(result[0].id, expected_first_id)

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
