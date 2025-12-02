"""Tests for TimeTracker domain service."""

from datetime import datetime

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.services.time_tracker import TimeTracker


class TestTimeTracker:
    """Test cases for TimeTracker."""

    @pytest.fixture
    def tracker(self):
        """Create a TimeTracker instance for each test."""
        return TimeTracker()

    @pytest.mark.parametrize(
        "new_status,field_name",
        [
            (TaskStatus.IN_PROGRESS, "actual_start"),
            (TaskStatus.COMPLETED, "actual_end"),
            (TaskStatus.CANCELED, "actual_end"),
        ],
        ids=[
            "in_progress_sets_actual_start",
            "completed_sets_actual_end",
            "canceled_sets_actual_end",
        ],
    )
    def test_record_time_on_status_change_sets_timestamps(
        self, tracker, new_status, field_name
    ):
        """Test that appropriate timestamps are recorded for different status changes."""
        task = Task(name="Test Task", priority=1, id=1)
        assert getattr(task, field_name) is None

        tracker.record_time_on_status_change(task, new_status)

        assert getattr(task, field_name) is not None
        assert isinstance(getattr(task, field_name), datetime)

    def test_no_record_for_pending(self, tracker):
        """Test that no timestamps are recorded for PENDING status."""
        task = Task(name="Test Task", priority=1, id=1)

        tracker.record_time_on_status_change(task, TaskStatus.PENDING)

        assert task.actual_start is None
        assert task.actual_end is None

    def test_do_not_overwrite_existing_actual_start(self, tracker):
        """Test that existing actual_start is not overwritten."""
        original_start = datetime(2025, 1, 1, 10, 0, 0)
        task = Task(name="Test Task", priority=1, id=1, actual_start=original_start)

        tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)

        assert task.actual_start == original_start

    def test_do_not_overwrite_existing_actual_end(self, tracker):
        """Test that existing actual_end is not overwritten."""
        original_end = datetime(2025, 1, 1, 18, 0, 0)
        task = Task(name="Test Task", priority=1, id=1, actual_end=original_end)

        tracker.record_time_on_status_change(task, TaskStatus.COMPLETED)

        assert task.actual_end == original_end

    def test_workflow_pending_to_in_progress_to_completed(self, tracker):
        """Test a complete workflow: PENDING -> IN_PROGRESS -> COMPLETED."""
        task = Task(name="Test Task", priority=1, id=1, status=TaskStatus.PENDING)

        # Start the task
        tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)
        assert task.actual_start is not None
        assert task.actual_end is None

        # Complete the task
        tracker.record_time_on_status_change(task, TaskStatus.COMPLETED)
        assert task.actual_start is not None
        assert task.actual_end is not None

    def test_workflow_pending_to_completed_without_in_progress(self, tracker):
        """Test completing a task without going through IN_PROGRESS."""
        task = Task(name="Test Task", priority=1, id=1, status=TaskStatus.PENDING)

        tracker.record_time_on_status_change(task, TaskStatus.COMPLETED)

        # Only actual_end should be set
        assert task.actual_start is None
        assert task.actual_end is not None

    def test_timestamp_is_datetime_object(self, tracker):
        """Test that timestamps are datetime objects."""
        task = Task(name="Test Task", priority=1, id=1)

        tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)

        # Should be a datetime object
        assert isinstance(task.actual_start, datetime)

    def test_multiple_status_changes(self, tracker):
        """Test multiple status changes don't overwrite original timestamps."""
        task = Task(name="Test Task", priority=1, id=1)

        # First transition: PENDING -> IN_PROGRESS
        tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)
        original_start = task.actual_start

        # Second transition: IN_PROGRESS -> PENDING (paused)
        tracker.record_time_on_status_change(task, TaskStatus.PENDING)

        # Third transition: PENDING -> IN_PROGRESS (resumed)
        tracker.record_time_on_status_change(task, TaskStatus.IN_PROGRESS)

        # Original start time should be preserved
        assert task.actual_start == original_start

    @pytest.mark.parametrize(
        "actual_start,actual_end",
        [
            (datetime(2025, 1, 1, 10, 0, 0), datetime(2025, 1, 1, 18, 0, 0)),
            (datetime(2025, 1, 1, 10, 0, 0), None),
            (None, None),
        ],
        ids=[
            "both_timestamps_set",
            "only_actual_start_set",
            "no_timestamps_set",
        ],
    )
    def test_clear_time_tracking_handles_all_scenarios(
        self, tracker, actual_start, actual_end
    ):
        """Test that clear_time_tracking clears timestamps in various scenarios."""
        task = Task(
            name="Test Task",
            priority=1,
            id=1,
            actual_start=actual_start,
            actual_end=actual_end,
        )

        tracker.clear_time_tracking(task)

        assert task.actual_start is None
        assert task.actual_end is None
