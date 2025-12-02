"""Tests for TaskFilter base class."""

import pytest

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


class TestTaskFilter:
    """Test cases for TaskFilter abstract base class."""

    def test_task_filter_is_abstract(self):
        """Test TaskFilter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TaskFilter()  # type: ignore[abstract]

    def test_concrete_filter_can_be_instantiated(self):
        """Test concrete implementation can be instantiated."""
        concrete_filter = ConcreteFilter()

        assert isinstance(concrete_filter, TaskFilter)

    def test_concrete_filter_has_filter_method(self):
        """Test concrete filter implements filter method."""
        concrete_filter = ConcreteFilter()

        assert hasattr(concrete_filter, "filter")
        assert callable(concrete_filter.filter)

    def test_filter_method_signature(self):
        """Test filter method has correct signature."""
        concrete_filter = ConcreteFilter()
        tasks: list[Task] = []

        # Should not raise
        result = concrete_filter.filter(tasks)

        assert isinstance(result, list)

    def test_rshift_operator_composes_filters(self):
        """Test >> operator creates a composite filter."""
        filter1 = PendingOnlyFilter()
        filter2 = HighPriorityFilter()

        composed = filter1 >> filter2

        assert isinstance(composed, CompositeFilter)
        assert len(composed.filters) == 2
        assert composed.filters[0] is filter1
        assert composed.filters[1] is filter2

    @pytest.mark.parametrize(
        "composed_factory,tasks_factory,expected_count,expected_id",
        [
            (
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
                lambda: ConcreteFilter() >> PendingOnlyFilter() >> HighPriorityFilter(),
                lambda: [
                    Task(id=1, name="Task 1", status=TaskStatus.PENDING, priority=5),
                    Task(id=2, name="Task 2", status=TaskStatus.PENDING, priority=3),
                ],
                1,
                1,
            ),
        ],
        ids=["two_filters_sequence", "three_filters_chain"],
    )
    def test_rshift_operator_filter_execution(
        self, composed_factory, tasks_factory, expected_count, expected_id
    ):
        """Test >> operator applies filters in sequence."""
        composed = composed_factory()
        tasks = tasks_factory()
        result = composed.filter(tasks)

        assert len(result) == expected_count
        assert result[0].id == expected_id

    def test_rshift_operator_with_none_returns_self(self):
        """Test >> operator with None returns self."""
        filter1 = PendingOnlyFilter()

        result = filter1 >> None

        assert result is filter1

    @pytest.mark.parametrize(
        "composed_factory,expected_filter_count",
        [
            (
                lambda: (PendingOnlyFilter() >> HighPriorityFilter())
                >> ConcreteFilter(),
                3,
            ),
            (
                lambda: PendingOnlyFilter()
                >> (HighPriorityFilter() >> ConcreteFilter()),
                3,
            ),
        ],
        ids=["extend_composite", "composite_on_right"],
    )
    def test_rshift_operator_composite_composition(
        self, composed_factory, expected_filter_count
    ):
        """Test >> operator composition with CompositeFilters."""
        composed = composed_factory()

        assert isinstance(composed, CompositeFilter)
        assert len(composed.filters) == expected_filter_count
