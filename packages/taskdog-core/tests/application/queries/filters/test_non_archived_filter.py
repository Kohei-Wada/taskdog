"""Tests for NonArchivedFilter."""

import pytest

from taskdog_core.application.queries.filters.non_archived_filter import (
    NonArchivedFilter,
)
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestNonArchivedFilter:
    """Test cases for NonArchivedFilter."""

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

    @pytest.mark.parametrize(
        "status_attr",
        ["task_pending", "task_in_progress", "task_completed", "task_canceled"],
        ids=["pending", "in_progress", "completed", "canceled"],
    )
    def test_filter_includes_each_non_archived_status(self, status_attr):
        """Test filter includes all non-archived statuses."""
        non_archived_filter = NonArchivedFilter()
        task = getattr(self, status_attr)
        result = non_archived_filter.filter([task])

        assert len(result) == 1
        assert result[0] == task

    def test_filter_includes_all_non_archived_statuses(self):
        """Test filter includes all non-archived tasks."""
        non_archived_filter = NonArchivedFilter()
        tasks = [
            self.task_pending,
            self.task_in_progress,
            self.task_completed,
            self.task_canceled,
        ]

        result = non_archived_filter.filter(tasks)

        assert len(result) == 4

    def test_filter_with_empty_list(self):
        """Test filter with empty task list."""
        non_archived_filter = NonArchivedFilter()
        result = non_archived_filter.filter([])

        assert len(result) == 0
