"""Tests for StatusFilter."""

import pytest

from taskdog_core.application.queries.filters.status_filter import StatusFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestStatusFilter:
    """Test cases for StatusFilter."""

    @pytest.fixture(autouse=True)
    def setup(self):
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

    @pytest.mark.parametrize(
        "status,expected_id",
        [
            (TaskStatus.PENDING, 1),
            (TaskStatus.IN_PROGRESS, 2),
            (TaskStatus.COMPLETED, 3),
            (TaskStatus.CANCELED, 4),
        ],
        ids=["pending", "in_progress", "completed", "canceled"],
    )
    def test_filter_by_each_status(self, status, expected_id):
        """Test filter returns only tasks matching each status."""
        status_filter = StatusFilter(status)
        result = status_filter.filter(self.tasks)

        assert len(result) == 1
        assert result[0].id == expected_id
        assert result[0].status == status

    def test_filter_with_multiple_matching_tasks(self):
        """Test filter with multiple tasks of same status."""
        task_pending_2 = Task(
            id=5, name="Pending 2", status=TaskStatus.PENDING, priority=2
        )
        tasks = [self.task_pending, self.task_in_progress, task_pending_2]

        status_filter = StatusFilter(TaskStatus.PENDING)
        result = status_filter.filter(tasks)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 5

    def test_filter_with_no_matching_tasks(self):
        """Test filter with no tasks matching the status."""
        tasks = [self.task_in_progress]

        status_filter = StatusFilter(TaskStatus.PENDING)
        result = status_filter.filter(tasks)

        assert len(result) == 0

    def test_filter_with_empty_list(self):
        """Test filter with empty task list."""
        status_filter = StatusFilter(TaskStatus.PENDING)
        result = status_filter.filter([])

        assert len(result) == 0

    def test_filter_stores_status(self):
        """Test that filter stores the target status."""
        status_filter = StatusFilter(TaskStatus.COMPLETED)

        assert status_filter.status == TaskStatus.COMPLETED
