"""Tests for TaskStatusService."""

import tempfile
import unittest

from application.services.task_status_service import TaskStatusService
from domain.entities.task import TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TaskStatusServiceTest(unittest.TestCase):
    """Test cases for TaskStatusService."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.temp_file.write("[]")
        self.temp_file.close()

        self.repository = JsonTaskRepository(self.temp_file.name)
        self.time_tracker = TimeTracker()
        self.service = TaskStatusService()

    def test_change_status_to_in_progress(self):
        """Test changing status to IN_PROGRESS records actual_start."""
        # Create a pending task
        task = self.repository.create(name="Test Task", priority=1)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.actual_start)

        # Change to IN_PROGRESS
        updated = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )

        # Verify status changed and actual_start recorded
        self.assertEqual(updated.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(updated.actual_start)
        self.assertIsNone(updated.actual_end)

        # Verify persisted
        from_db = self.repository.get_by_id(task.id)
        self.assertEqual(from_db.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(from_db.actual_start)

    def test_change_status_to_completed(self):
        """Test changing status to COMPLETED records actual_end."""
        # Create a task and start it
        task = self.repository.create(name="Test Task", priority=1)
        task = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )
        self.assertIsNotNone(task.actual_start)
        self.assertIsNone(task.actual_end)

        # Complete the task
        updated = self.service.change_status_with_tracking(
            task, TaskStatus.COMPLETED, self.time_tracker, self.repository
        )

        # Verify status changed and actual_end recorded
        self.assertEqual(updated.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(updated.actual_start)
        self.assertIsNotNone(updated.actual_end)

        # Verify persisted
        from_db = self.repository.get_by_id(task.id)
        self.assertEqual(from_db.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(from_db.actual_end)

    def test_change_status_to_canceled(self):
        """Test changing status to CANCELED records actual_end."""
        # Create a task and start it
        task = self.repository.create(name="Test Task", priority=1)
        task = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )

        # Cancel the task
        updated = self.service.change_status_with_tracking(
            task, TaskStatus.CANCELED, self.time_tracker, self.repository
        )

        # Verify status changed and actual_end recorded
        self.assertEqual(updated.status, TaskStatus.CANCELED)
        self.assertIsNotNone(updated.actual_start)
        self.assertIsNotNone(updated.actual_end)

        # Verify persisted
        from_db = self.repository.get_by_id(task.id)
        self.assertEqual(from_db.status, TaskStatus.CANCELED)
        self.assertIsNotNone(from_db.actual_end)

    def test_change_status_multiple_times(self):
        """Test changing status multiple times."""
        task = self.repository.create(name="Test Task", priority=1)

        # PENDING -> IN_PROGRESS
        task = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(task.actual_start)

        # IN_PROGRESS -> PENDING (restart)
        task = self.service.change_status_with_tracking(
            task, TaskStatus.PENDING, self.time_tracker, self.repository
        )
        self.assertEqual(task.status, TaskStatus.PENDING)

        # PENDING -> IN_PROGRESS again
        task = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        # actual_start should be updated to new start time
        self.assertIsNotNone(task.actual_start)

        # Finally complete
        task = self.service.change_status_with_tracking(
            task, TaskStatus.COMPLETED, self.time_tracker, self.repository
        )
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.actual_end)

    def test_change_status_preserves_other_fields(self):
        """Test that changing status doesn't affect other task fields."""
        # Create task with various fields
        task = self.repository.create(
            name="Test Task",
            priority=5,
            planned_start="2025-10-20 09:00:00",
            planned_end="2025-10-21 18:00:00",
            deadline="2025-10-22 18:00:00",
            estimated_duration=8.0,
        )

        # Change status
        updated = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )

        # Verify other fields preserved
        self.assertEqual(updated.name, "Test Task")
        self.assertEqual(updated.priority, 5)
        self.assertEqual(updated.planned_start, "2025-10-20 09:00:00")
        self.assertEqual(updated.planned_end, "2025-10-21 18:00:00")
        self.assertEqual(updated.deadline, "2025-10-22 18:00:00")
        self.assertEqual(updated.estimated_duration, 8.0)

    def test_change_status_returns_same_task_object(self):
        """Test that the method returns the same task object (mutated)."""
        task = self.repository.create(name="Test Task", priority=1)
        original_id = id(task)

        updated = self.service.change_status_with_tracking(
            task, TaskStatus.IN_PROGRESS, self.time_tracker, self.repository
        )

        # Should return the same object
        self.assertEqual(id(updated), original_id)


if __name__ == "__main__":
    unittest.main()
