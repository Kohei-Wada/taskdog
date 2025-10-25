"""Tests for Task entity business logic methods."""

import unittest
from datetime import datetime

from domain.entities.task import Task, TaskStatus


class TestTaskIsSchedulable(unittest.TestCase):
    """Test cases for Task.is_schedulable() method."""

    def test_is_schedulable_with_pending_task_and_duration(self):
        """Test that PENDING task with estimated_duration is schedulable."""
        task = Task(
            name="Test Task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
        )

        result = task.is_schedulable(force_override=False)

        self.assertTrue(result)

    def test_is_not_schedulable_with_completed_task(self):
        """Test that COMPLETED tasks are not schedulable."""
        task = Task(
            name="Completed task",
            priority=100,
            status=TaskStatus.COMPLETED,
            estimated_duration=4.0,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_not_schedulable_with_deleted_task(self):
        """Test that deleted tasks are not schedulable."""
        task = Task(
            name="Deleted task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            is_deleted=True,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_not_schedulable_with_in_progress_task(self):
        """Test that IN_PROGRESS tasks are not reschedulable."""
        task = Task(
            name="In-progress task",
            priority=100,
            status=TaskStatus.IN_PROGRESS,
            estimated_duration=4.0,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_not_schedulable_without_duration(self):
        """Test that tasks without estimated_duration are not schedulable."""
        task = Task(
            name="Task without duration",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=None,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_not_schedulable_with_existing_schedule_by_default(self):
        """Test that tasks with existing schedules are not schedulable by default."""
        task = Task(
            name="Scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            planned_start="2025-01-06 09:00:00",
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)

    def test_is_schedulable_with_existing_schedule_when_forced(self):
        """Test that tasks with existing schedules are schedulable with force_override."""
        task = Task(
            name="Scheduled task",
            priority=100,
            status=TaskStatus.PENDING,
            estimated_duration=4.0,
            planned_start="2025-01-06 09:00:00",
        )

        result = task.is_schedulable(force_override=True)

        self.assertTrue(result)

    def test_is_not_schedulable_with_canceled_status(self):
        """Test that CANCELED tasks are not schedulable."""
        task = Task(
            name="Canceled task",
            priority=100,
            status=TaskStatus.CANCELED,
            estimated_duration=4.0,
        )

        result = task.is_schedulable(force_override=False)

        self.assertFalse(result)


class TestTaskShouldCountInWorkload(unittest.TestCase):
    """Test cases for Task.should_count_in_workload() method."""

    def test_pending_task_counts_in_workload(self):
        """Test that PENDING tasks count in workload."""
        task = Task(
            name="Pending task",
            priority=100,
            status=TaskStatus.PENDING,
        )

        result = task.should_count_in_workload()

        self.assertTrue(result)

    def test_in_progress_task_counts_in_workload(self):
        """Test that IN_PROGRESS tasks count in workload."""
        task = Task(
            name="In-progress task",
            priority=100,
            status=TaskStatus.IN_PROGRESS,
        )

        result = task.should_count_in_workload()

        self.assertTrue(result)

    def test_completed_task_does_not_count_in_workload(self):
        """Test that COMPLETED tasks do not count in workload."""
        task = Task(
            name="Completed task",
            priority=100,
            status=TaskStatus.COMPLETED,
        )

        result = task.should_count_in_workload()

        self.assertFalse(result)

    def test_canceled_task_does_not_count_in_workload(self):
        """Test that CANCELED tasks do not count in workload."""
        task = Task(
            name="Canceled task",
            priority=100,
            status=TaskStatus.CANCELED,
        )

        result = task.should_count_in_workload()

        self.assertFalse(result)


class TestTaskSerialization(unittest.TestCase):
    """Test cases for Task serialization methods."""

    def test_serialize_datetime_with_datetime_object(self):
        """Test that _serialize_datetime converts datetime to ISO string."""
        dt = datetime(2025, 1, 15, 10, 30, 0)

        result = Task._serialize_datetime(dt)

        self.assertEqual(result, "2025-01-15T10:30:00")

    def test_serialize_datetime_with_none(self):
        """Test that _serialize_datetime returns None for None input."""
        result = Task._serialize_datetime(None)

        self.assertIsNone(result)

    def test_serialize_datetime_with_string(self):
        """Test that _serialize_datetime returns string unchanged."""
        dt_string = "2025-01-15T10:30:00"

        result = Task._serialize_datetime(dt_string)

        self.assertEqual(result, dt_string)

    def test_to_dict_serializes_datetime_fields(self):
        """Test that to_dict properly serializes datetime fields."""
        task = Task(
            name="Test Task",
            priority=1,
            id=1,
            created_at=datetime(2025, 1, 1, 0, 0, 0),
            updated_at=datetime(2025, 1, 2, 0, 0, 0),
            planned_start=datetime(2025, 1, 15, 10, 0, 0),
            planned_end=datetime(2025, 1, 15, 12, 0, 0),
            deadline=datetime(2025, 1, 20, 18, 0, 0),
            actual_start=datetime(2025, 1, 15, 10, 5, 0),
            actual_end=datetime(2025, 1, 15, 11, 50, 0),
        )

        result = task.to_dict()

        self.assertEqual(result["created_at"], "2025-01-01T00:00:00")
        self.assertEqual(result["updated_at"], "2025-01-02T00:00:00")
        self.assertEqual(result["planned_start"], "2025-01-15T10:00:00")
        self.assertEqual(result["planned_end"], "2025-01-15T12:00:00")
        self.assertEqual(result["deadline"], "2025-01-20T18:00:00")
        self.assertEqual(result["actual_start"], "2025-01-15T10:05:00")
        self.assertEqual(result["actual_end"], "2025-01-15T11:50:00")

    def test_to_dict_handles_none_datetime_fields(self):
        """Test that to_dict handles None datetime fields correctly."""
        task = Task(name="Test Task", priority=1, id=1)

        result = task.to_dict()

        self.assertIsNone(result["planned_start"])
        self.assertIsNone(result["planned_end"])
        self.assertIsNone(result["deadline"])
        self.assertIsNone(result["actual_start"])
        self.assertIsNone(result["actual_end"])

    def test_from_dict_backward_compatibility_without_updated_at(self):
        """Test that from_dict uses created_at when updated_at is missing."""
        created = datetime(2025, 1, 1, 0, 0, 0)
        task_data = {
            "id": 1,
            "name": "Test Task",
            "priority": 1,
            "status": "PENDING",
            "created_at": created.isoformat(),
            # updated_at is missing (old data format)
        }

        task = Task.from_dict(task_data)

        self.assertEqual(task.created_at, created)
        self.assertEqual(task.updated_at, created)

    def test_from_dict_with_updated_at(self):
        """Test that from_dict correctly deserializes updated_at."""
        created = datetime(2025, 1, 1, 0, 0, 0)
        updated = datetime(2025, 1, 2, 10, 30, 0)
        task_data = {
            "id": 1,
            "name": "Test Task",
            "priority": 1,
            "status": "PENDING",
            "created_at": created.isoformat(),
            "updated_at": updated.isoformat(),
        }

        task = Task.from_dict(task_data)

        self.assertEqual(task.created_at, created)
        self.assertEqual(task.updated_at, updated)


if __name__ == "__main__":
    unittest.main()
