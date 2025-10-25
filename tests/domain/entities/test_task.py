"""Tests for Task entity business logic methods."""

import unittest
from datetime import datetime

from domain.entities.task import Task, TaskStatus


class TestTaskIsSchedulable(unittest.TestCase):
    """Test cases for Task.is_schedulable() method."""

    def test_is_schedulable_by_status_and_duration(self):
        """Test schedulability based on status and estimated_duration."""
        test_cases = [
            (TaskStatus.PENDING, 4.0, True, "PENDING with duration"),
            (TaskStatus.COMPLETED, 4.0, False, "COMPLETED task"),
            (TaskStatus.ARCHIVED, 4.0, False, "ARCHIVED task"),
            (TaskStatus.IN_PROGRESS, 4.0, False, "IN_PROGRESS task"),
            (TaskStatus.CANCELED, 4.0, False, "CANCELED task"),
            (TaskStatus.PENDING, None, False, "PENDING without duration"),
        ]
        for status, duration, expected, description in test_cases:
            with self.subTest(description=description):
                task = Task(
                    name="Test Task",
                    priority=100,
                    status=status,
                    estimated_duration=duration,
                )
                result = task.is_schedulable(force_override=False)
                self.assertEqual(result, expected)

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


class TestTaskShouldCountInWorkload(unittest.TestCase):
    """Test cases for Task.should_count_in_workload() method."""

    def test_should_count_in_workload_by_status(self):
        """Test workload counting based on task status."""
        test_cases = [
            (TaskStatus.PENDING, True, "PENDING task"),
            (TaskStatus.IN_PROGRESS, True, "IN_PROGRESS task"),
            (TaskStatus.COMPLETED, False, "COMPLETED task"),
            (TaskStatus.CANCELED, False, "CANCELED task"),
        ]
        for status, expected, description in test_cases:
            with self.subTest(description=description):
                task = Task(name="Test task", priority=100, status=status)
                result = task.should_count_in_workload()
                self.assertEqual(result, expected)


class TestTaskSerialization(unittest.TestCase):
    """Test cases for Task serialization methods."""

    def test_serialize_datetime(self):
        """Test _serialize_datetime handles various input types."""
        test_cases = [
            (datetime(2025, 1, 15, 10, 30, 0), "2025-01-15T10:30:00", "datetime object"),
            (None, None, "None input"),
            ("2025-01-15T10:30:00", "2025-01-15T10:30:00", "string input"),
        ]
        for input_value, expected, description in test_cases:
            with self.subTest(description=description):
                result = Task._serialize_datetime(input_value)
                self.assertEqual(result, expected)

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
