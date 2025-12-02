"""Tests for TaskStatusService."""

from datetime import datetime

import pytest

from taskdog_core.application.services.task_status_service import TaskStatusService
from taskdog_core.domain.entities.task import TaskStatus


class TestTaskStatusService:
    """Test cases for TaskStatusService."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Set up test fixtures."""
        self.repository = repository
        self.service = TaskStatusService()

    def test_change_status_to_in_progress(self):
        """Test changing status to IN_PROGRESS records actual_start."""
        # Create a pending task
        task = self.repository.create(name="Test Task", priority=1)
        assert task.status == TaskStatus.PENDING
        assert task.actual_start is None

        # Change to IN_PROGRESS
        updated = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.repository
        )

        # Verify status changed and actual_start recorded
        assert updated.status == TaskStatus.IN_PROGRESS
        assert updated.actual_start is not None
        assert updated.actual_end is None

        # Verify persisted
        from_db = self.repository.get_by_id(task.id)
        assert from_db.status == TaskStatus.IN_PROGRESS
        assert from_db.actual_start is not None

    def test_change_status_to_completed(self):
        """Test changing status to COMPLETED records actual_end."""
        # Create a task and start it
        task = self.repository.create(name="Test Task", priority=1)
        task = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.repository
        )
        assert task.actual_start is not None
        assert task.actual_end is None

        # Complete the task
        updated = self.service.change_status_with_tracking(
            task, TaskStatus.COMPLETED, self.repository
        )

        # Verify status changed and actual_end recorded
        assert updated.status == TaskStatus.COMPLETED
        assert updated.actual_start is not None
        assert updated.actual_end is not None

        # Verify persisted
        from_db = self.repository.get_by_id(task.id)
        assert from_db.status == TaskStatus.COMPLETED
        assert from_db.actual_end is not None

    def test_change_status_to_canceled(self):
        """Test changing status to CANCELED records actual_end."""
        # Create a task and start it
        task = self.repository.create(name="Test Task", priority=1)
        task = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.repository
        )

        # Cancel the task
        updated = self.service.change_status_with_tracking(
            task, TaskStatus.CANCELED, self.repository
        )

        # Verify status changed and actual_end recorded
        assert updated.status == TaskStatus.CANCELED
        assert updated.actual_start is not None
        assert updated.actual_end is not None

        # Verify persisted
        from_db = self.repository.get_by_id(task.id)
        assert from_db.status == TaskStatus.CANCELED
        assert from_db.actual_end is not None

    def test_change_status_multiple_times(self):
        """Test changing status multiple times."""
        task = self.repository.create(name="Test Task", priority=1)

        # PENDING -> IN_PROGRESS
        task = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.repository
        )
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.actual_start is not None

        # IN_PROGRESS -> PENDING (restart)
        task = self.service.change_status_with_tracking(
            task, TaskStatus.PENDING, self.repository
        )
        assert task.status == TaskStatus.PENDING

        # PENDING -> IN_PROGRESS again
        task = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.repository
        )
        assert task.status == TaskStatus.IN_PROGRESS
        # actual_start should be updated to new start time
        assert task.actual_start is not None

        # Finally complete
        task = self.service.change_status_with_tracking(
            task, TaskStatus.COMPLETED, self.repository
        )
        assert task.status == TaskStatus.COMPLETED
        assert task.actual_end is not None

    def test_change_status_preserves_other_fields(self):
        """Test that changing status doesn't affect other task fields."""
        # Create task with various fields
        task = self.repository.create(
            name="Test Task",
            priority=5,
            planned_start=datetime(2025, 10, 20, 9, 0, 0),
            planned_end=datetime(2025, 10, 21, 18, 0, 0),
            deadline=datetime(2025, 10, 22, 18, 0, 0),
            estimated_duration=8.0,
        )

        # Change status
        updated = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.repository
        )

        # Verify other fields preserved
        assert updated.name == "Test Task"
        assert updated.priority == 5
        assert updated.planned_start == datetime(2025, 10, 20, 9, 0, 0)
        assert updated.planned_end == datetime(2025, 10, 21, 18, 0, 0)
        assert updated.deadline == datetime(2025, 10, 22, 18, 0, 0)
        assert updated.estimated_duration == 8.0

    def test_change_status_returns_same_task_object(self):
        """Test that the method returns the same task object (mutated)."""
        task = self.repository.create(name="Test Task", priority=1)
        original_id = id(task)

        updated = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.repository
        )

        # Should return the same object
        assert id(updated) == original_id
