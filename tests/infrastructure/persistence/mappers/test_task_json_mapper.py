"""Tests for TaskJsonMapper."""

import unittest
from datetime import date, datetime

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.mappers.task_json_mapper import TaskJsonMapper


class TestTaskJsonMapper(unittest.TestCase):
    """Test cases for TaskJsonMapper serialization and deserialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = TaskJsonMapper()

    def test_to_dict_serializes_all_fields(self):
        """Test that to_dict properly serializes all task fields."""
        task = Task(
            name="Test Task",
            priority=1,
            id=1,
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime(2025, 1, 1, 0, 0, 0),
            updated_at=datetime(2025, 1, 2, 0, 0, 0),
            planned_start=datetime(2025, 1, 15, 10, 0, 0),
            planned_end=datetime(2025, 1, 15, 12, 0, 0),
            deadline=datetime(2025, 1, 20, 18, 0, 0),
            actual_start=datetime(2025, 1, 15, 10, 5, 0),
            actual_end=datetime(2025, 1, 15, 11, 50, 0),
            estimated_duration=2.0,
            is_fixed=True,
            depends_on=[2, 3],
            daily_allocations={date(2025, 1, 15): 2.0},
            actual_daily_hours={date(2025, 1, 15): 1.5},
            tags=["urgent", "backend"],
            is_archived=False,
        )

        result = self.mapper.to_dict(task)

        # Check basic fields
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["name"], "Test Task")
        self.assertEqual(result["priority"], 1)
        self.assertEqual(result["status"], "IN_PROGRESS")
        self.assertEqual(result["estimated_duration"], 2.0)
        self.assertEqual(result["is_fixed"], True)
        self.assertEqual(result["depends_on"], [2, 3])
        self.assertEqual(result["tags"], ["urgent", "backend"])
        self.assertEqual(result["is_archived"], False)

        # Check datetime serialization
        self.assertEqual(result["created_at"], "2025-01-01T00:00:00")
        self.assertEqual(result["updated_at"], "2025-01-02T00:00:00")
        self.assertEqual(result["planned_start"], "2025-01-15T10:00:00")
        self.assertEqual(result["planned_end"], "2025-01-15T12:00:00")
        self.assertEqual(result["deadline"], "2025-01-20T18:00:00")
        self.assertEqual(result["actual_start"], "2025-01-15T10:05:00")
        self.assertEqual(result["actual_end"], "2025-01-15T11:50:00")

        # Check date-based dictionaries
        self.assertEqual(result["daily_allocations"], {"2025-01-15": 2.0})
        self.assertEqual(result["actual_daily_hours"], {"2025-01-15": 1.5})

    def test_to_dict_handles_none_datetime_fields(self):
        """Test that to_dict handles None datetime fields correctly."""
        task = Task(name="Test Task", priority=1, id=1)

        result = self.mapper.to_dict(task)

        self.assertIsNone(result["planned_start"])
        self.assertIsNone(result["planned_end"])
        self.assertIsNone(result["deadline"])
        self.assertIsNone(result["actual_start"])
        self.assertIsNone(result["actual_end"])

    def test_to_dict_handles_empty_collections(self):
        """Test that to_dict handles empty dictionaries and lists."""
        task = Task(name="Test Task", priority=1, id=1)

        result = self.mapper.to_dict(task)

        self.assertEqual(result["depends_on"], [])
        self.assertEqual(result["daily_allocations"], {})
        self.assertEqual(result["actual_daily_hours"], {})
        self.assertEqual(result["tags"], [])

    def test_from_dict_deserializes_all_fields(self):
        """Test that from_dict correctly deserializes all task fields."""
        task_data = {
            "id": 1,
            "name": "Test Task",
            "priority": 1,
            "status": "IN_PROGRESS",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            "planned_start": "2025-01-15T10:00:00",
            "planned_end": "2025-01-15T12:00:00",
            "deadline": "2025-01-20T18:00:00",
            "actual_start": "2025-01-15T10:05:00",
            "actual_end": "2025-01-15T11:50:00",
            "estimated_duration": 2.0,
            "is_fixed": True,
            "depends_on": [2, 3],
            "daily_allocations": {"2025-01-15": 2.0},
            "actual_daily_hours": {"2025-01-15": 1.5},
            "tags": ["urgent", "backend"],
            "is_archived": False,
        }

        task = self.mapper.from_dict(task_data)

        # Check basic fields
        self.assertEqual(task.id, 1)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, 1)
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(task.estimated_duration, 2.0)
        self.assertEqual(task.is_fixed, True)
        self.assertEqual(task.depends_on, [2, 3])
        self.assertEqual(task.tags, ["urgent", "backend"])
        self.assertEqual(task.is_archived, False)

        # Check datetime deserialization
        self.assertEqual(task.created_at, datetime(2025, 1, 1, 0, 0, 0))
        self.assertEqual(task.updated_at, datetime(2025, 1, 2, 0, 0, 0))
        self.assertEqual(task.planned_start, datetime(2025, 1, 15, 10, 0, 0))
        self.assertEqual(task.planned_end, datetime(2025, 1, 15, 12, 0, 0))
        self.assertEqual(task.deadline, datetime(2025, 1, 20, 18, 0, 0))
        self.assertEqual(task.actual_start, datetime(2025, 1, 15, 10, 5, 0))
        self.assertEqual(task.actual_end, datetime(2025, 1, 15, 11, 50, 0))

        # Check date-based dictionaries
        self.assertEqual(task.daily_allocations, {date(2025, 1, 15): 2.0})
        self.assertEqual(task.actual_daily_hours, {date(2025, 1, 15): 1.5})

    def test_from_dict_backward_compatibility_is_deleted(self):
        """Test backward compatibility: is_deleted migrates to is_archived."""
        task_data = {
            "id": 1,
            "name": "Test Task",
            "priority": 1,
            "status": "PENDING",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            "is_deleted": True,  # Legacy field
        }

        task = self.mapper.from_dict(task_data)

        self.assertTrue(task.is_archived)
        # is_deleted should be removed from task_data after processing
        self.assertFalse(hasattr(task, "is_deleted"))

    def test_from_dict_backward_compatibility_missing_fields(self):
        """Test backward compatibility: missing fields get default values."""
        task_data = {
            "id": 1,
            "name": "Test Task",
            "priority": 1,
            "status": "PENDING",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-02T00:00:00",
            # Missing is_archived and tags fields
        }

        task = self.mapper.from_dict(task_data)

        self.assertFalse(task.is_archived)
        self.assertEqual(task.tags, [])

    def test_roundtrip_serialization_preserves_data(self):
        """Test that serializing and deserializing preserves all data."""
        original_task = Task(
            name="Test Task",
            priority=1,
            id=1,
            status=TaskStatus.COMPLETED,
            created_at=datetime(2025, 1, 1, 0, 0, 0),
            updated_at=datetime(2025, 1, 2, 0, 0, 0),
            planned_start=datetime(2025, 1, 15, 10, 0, 0),
            planned_end=datetime(2025, 1, 15, 12, 0, 0),
            deadline=datetime(2025, 1, 20, 18, 0, 0),
            actual_start=datetime(2025, 1, 15, 10, 5, 0),
            actual_end=datetime(2025, 1, 15, 11, 50, 0),
            estimated_duration=2.0,
            is_fixed=True,
            depends_on=[2, 3],
            daily_allocations={date(2025, 1, 15): 2.0, date(2025, 1, 16): 3.0},
            actual_daily_hours={date(2025, 1, 15): 1.5},
            tags=["urgent", "backend"],
            is_archived=False,
        )

        # Serialize
        task_dict = self.mapper.to_dict(original_task)

        # Deserialize
        restored_task = self.mapper.from_dict(task_dict)

        # Verify all fields match
        self.assertEqual(restored_task.id, original_task.id)
        self.assertEqual(restored_task.name, original_task.name)
        self.assertEqual(restored_task.priority, original_task.priority)
        self.assertEqual(restored_task.status, original_task.status)
        self.assertEqual(restored_task.created_at, original_task.created_at)
        self.assertEqual(restored_task.updated_at, original_task.updated_at)
        self.assertEqual(restored_task.planned_start, original_task.planned_start)
        self.assertEqual(restored_task.planned_end, original_task.planned_end)
        self.assertEqual(restored_task.deadline, original_task.deadline)
        self.assertEqual(restored_task.actual_start, original_task.actual_start)
        self.assertEqual(restored_task.actual_end, original_task.actual_end)
        self.assertEqual(restored_task.estimated_duration, original_task.estimated_duration)
        self.assertEqual(restored_task.is_fixed, original_task.is_fixed)
        self.assertEqual(restored_task.depends_on, original_task.depends_on)
        self.assertEqual(restored_task.daily_allocations, original_task.daily_allocations)
        self.assertEqual(restored_task.actual_daily_hours, original_task.actual_daily_hours)
        self.assertEqual(restored_task.tags, original_task.tags)
        self.assertEqual(restored_task.is_archived, original_task.is_archived)

    def test_serialize_datetime_helper(self):
        """Test _serialize_datetime handles various input types."""
        test_cases = [
            (datetime(2025, 1, 15, 10, 30, 0), "2025-01-15T10:30:00", "datetime object"),
            (None, None, "None input"),
            ("2025-01-15T10:30:00", "2025-01-15T10:30:00", "string input"),
        ]
        for input_value, expected, description in test_cases:
            with self.subTest(description=description):
                result = self.mapper._serialize_datetime(input_value)
                self.assertEqual(result, expected)

    def test_parse_datetime_string_helper(self):
        """Test _parse_datetime_string parses ISO format correctly."""
        test_cases = [
            ("2025-01-15T10:30:00", datetime(2025, 1, 15, 10, 30, 0), "valid ISO format"),
            (None, None, "None input"),
            ("", None, "empty string"),
            ("invalid", None, "invalid format"),
        ]
        for input_value, expected, description in test_cases:
            with self.subTest(description=description):
                result = self.mapper._parse_datetime_string(input_value)
                self.assertEqual(result, expected)

    def test_parse_date_dict_helper(self):
        """Test _parse_date_dict converts string keys to date objects."""
        input_dict = {
            "2025-01-15": 2.0,
            "2025-01-16": 3.0,
            "invalid-date": 1.0,  # Should be skipped
        }

        result = self.mapper._parse_date_dict(input_dict)

        expected = {
            date(2025, 1, 15): 2.0,
            date(2025, 1, 16): 3.0,
        }
        self.assertEqual(result, expected)

    def test_parse_date_dict_empty(self):
        """Test _parse_date_dict handles empty dictionary."""
        result = self.mapper._parse_date_dict({})
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
