"""Tests for IncompleteFilter."""

import pytest

from taskdog_core.application.queries.filters.incomplete_filter import IncompleteFilter
from taskdog_core.domain.entities.task import Task, TaskStatus


class TestIncompleteFilter:
    """Test cases for IncompleteFilter."""

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
        "status_attr,should_include",
        [
            ("task_pending", True),
            ("task_in_progress", True),
            ("task_completed", False),
            ("task_canceled", False),
        ],
        ids=[
            "pending_included",
            "in_progress_included",
            "completed_excluded",
            "canceled_excluded",
        ],
    )
    def test_filter_by_completion_status(self, status_attr, should_include):
        """Test filter includes incomplete and excludes complete tasks."""
        incomplete_filter = IncompleteFilter()
        task = getattr(self, status_attr)
        result = incomplete_filter.filter([task])

        if should_include:
            assert len(result) == 1
            assert result[0] == task
        else:
            assert len(result) == 0

    def test_filter_with_mixed_statuses(self):
        """Test filter with mix of complete and incomplete tasks."""
        incomplete_filter = IncompleteFilter()
        tasks = [
            self.task_pending,
            self.task_in_progress,
            self.task_completed,
            self.task_canceled,
        ]

        result = incomplete_filter.filter(tasks)

        assert len(result) == 2
        assert self.task_pending in result
        assert self.task_in_progress in result

    def test_filter_with_empty_list(self):
        """Test filter with empty task list."""
        incomplete_filter = IncompleteFilter()
        result = incomplete_filter.filter([])

        assert len(result) == 0

    def test_filter_uses_is_finished_property(self):
        """Test filter correctly uses Task.is_finished property."""
        incomplete_filter = IncompleteFilter()

        # is_finished should be False for PENDING and IN_PROGRESS
        assert not self.task_pending.is_finished
        assert not self.task_in_progress.is_finished

        # is_finished should be True for COMPLETED and CANCELED
        assert self.task_completed.is_finished
        assert self.task_canceled.is_finished

        # Filter should only include not is_finished
        tasks = [
            self.task_pending,
            self.task_in_progress,
            self.task_completed,
            self.task_canceled,
        ]
        result = incomplete_filter.filter(tasks)

        for task in result:
            assert not task.is_finished
