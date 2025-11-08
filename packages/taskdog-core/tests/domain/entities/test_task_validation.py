"""Tests for Task entity invariant validation."""

import unittest

from parameterized import parameterized

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskValidationError
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TaskValidationTest(unittest.TestCase):
    """Test Task entity invariant validation in __post_init__."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = TaskDbMapper()

    @parameterized.expand(
        [
            ("basic_task", {"name": "Test Task", "priority": 5}, "name", "Test Task"),
            ("basic_task", {"name": "Test Task", "priority": 5}, "priority", 5),
            (
                "with_estimated_duration",
                {"name": "Test Task", "priority": 5, "estimated_duration": 10.0},
                "estimated_duration",
                10.0,
            ),
            (
                "with_tags",
                {"name": "Test Task", "priority": 5, "tags": ["work", "urgent"]},
                "tags",
                ["work", "urgent"],
            ),
            (
                "with_none_estimated_duration",
                {"name": "Test Task", "priority": 5, "estimated_duration": None},
                "estimated_duration",
                None,
            ),
        ]
    )
    def test_valid_task_creation(
        self, scenario_name, task_kwargs, attr_name, expected_value
    ):
        """Test creating tasks with valid values."""
        task = Task(**task_kwargs)
        self.assertEqual(getattr(task, attr_name), expected_value)

    @parameterized.expand(
        [
            ("empty_tag", ["work", "", "urgent"], "Tag cannot be empty"),
            ("duplicate_tags", ["work", "urgent", "work"], "Tags must be unique"),
        ]
    )
    def test_invalid_tags(self, scenario_name, tags, expected_error):
        """Test that invalid tags raise TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="Test Task", priority=5, tags=tags)
        self.assertIn(expected_error, str(context.exception))

    @parameterized.expand(
        [
            ("empty_name", "", "Task name cannot be empty"),
            ("whitespace_only_name", "   ", "Task name cannot be empty"),
        ]
    )
    def test_invalid_name(self, scenario_name, name, expected_error):
        """Test that invalid task names raise TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name=name, priority=5)
        self.assertIn(expected_error, str(context.exception))

    @parameterized.expand(
        [
            ("zero_priority", 0, "Priority must be greater than 0"),
            ("negative_priority", -1, "Priority must be greater than 0"),
        ]
    )
    def test_invalid_priority(self, scenario_name, priority, expected_error):
        """Test that invalid priority values raise TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="Test Task", priority=priority)
        self.assertIn(expected_error, str(context.exception))

    @parameterized.expand(
        [
            ("zero_duration", 0.0, "Estimated duration must be greater than 0"),
            ("negative_duration", -5.0, "Estimated duration must be greater than 0"),
        ]
    )
    def test_invalid_estimated_duration(self, scenario_name, duration, expected_error):
        """Test that invalid estimated_duration values raise TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="Test Task", priority=5, estimated_duration=duration)
        self.assertIn(expected_error, str(context.exception))

    def test_from_dict_with_valid_data(self):
        """Test that from_dict works with valid data."""
        data = {
            "id": 1,
            "name": "Test Task",
            "priority": 5,
            "status": "PENDING",
            "estimated_duration": 10.0,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
        }
        task = self.mapper.from_dict(data)
        self.assertEqual(task.id, 1)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, 5)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.estimated_duration, 10.0)

    @parameterized.expand(
        [
            (
                "empty_name",
                {"id": 1, "name": "", "priority": 5, "status": "PENDING"},
                "Task name cannot be empty",
            ),
            (
                "zero_priority",
                {"id": 1, "name": "Test Task", "priority": 0, "status": "PENDING"},
                "Priority must be greater than 0",
            ),
            (
                "negative_priority",
                {"id": 1, "name": "Test Task", "priority": -100, "status": "PENDING"},
                "Priority must be greater than 0",
            ),
            (
                "zero_estimated_duration",
                {
                    "id": 1,
                    "name": "Test Task",
                    "priority": 5,
                    "status": "PENDING",
                    "estimated_duration": 0.0,
                },
                "Estimated duration must be greater than 0",
            ),
            (
                "negative_estimated_duration",
                {
                    "id": 1,
                    "name": "Test Task",
                    "priority": 5,
                    "status": "PENDING",
                    "estimated_duration": -5.0,
                },
                "Estimated duration must be greater than 0",
            ),
        ]
    )
    def test_from_dict_validation_errors(
        self, scenario_name, task_dict, expected_error
    ):
        """Test that from_dict raises validation errors for invalid fields."""
        # Add required timestamp fields
        data = {
            **task_dict,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
        }
        with self.assertRaises(TaskValidationError) as context:
            self.mapper.from_dict(data)
        self.assertIn(expected_error, str(context.exception))


if __name__ == "__main__":
    unittest.main()
