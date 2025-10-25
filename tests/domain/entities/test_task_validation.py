"""Tests for Task entity invariant validation."""

import unittest

from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskValidationError


class TaskValidationTest(unittest.TestCase):
    """Test Task entity invariant validation in __post_init__."""

    def test_valid_task_creation(self):
        """Test creating a task with valid values."""
        task = Task(name="Test Task", priority=5)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, 5)

    def test_valid_task_with_estimated_duration(self):
        """Test creating a task with valid estimated_duration."""
        task = Task(name="Test Task", priority=5, estimated_duration=10.0)
        self.assertEqual(task.estimated_duration, 10.0)

    def test_invalid_name_raises_error(self):
        """Test that invalid task names raise TaskValidationError."""
        test_cases = [
            ("", "empty name"),
            ("   ", "whitespace-only name"),
        ]
        for name, description in test_cases:
            with self.subTest(description=description):
                with self.assertRaises(TaskValidationError) as context:
                    Task(name=name, priority=5)
                self.assertIn("Task name cannot be empty", str(context.exception))

    def test_invalid_priority_raises_error(self):
        """Test that invalid priority values raise TaskValidationError."""
        test_cases = [
            (0, "zero priority"),
            (-1, "negative priority"),
        ]
        for priority, description in test_cases:
            with self.subTest(description=description):
                with self.assertRaises(TaskValidationError) as context:
                    Task(name="Test Task", priority=priority)
                self.assertIn("Priority must be greater than 0", str(context.exception))

    def test_invalid_estimated_duration_raises_error(self):
        """Test that invalid estimated_duration values raise TaskValidationError."""
        test_cases = [
            (0.0, "zero duration"),
            (-5.0, "negative duration"),
        ]
        for duration, description in test_cases:
            with self.subTest(description=description):
                with self.assertRaises(TaskValidationError) as context:
                    Task(name="Test Task", priority=5, estimated_duration=duration)
                self.assertIn("Estimated duration must be greater than 0", str(context.exception))

    def test_none_estimated_duration_is_valid(self):
        """Test that None estimated_duration is valid (optional field)."""
        task = Task(name="Test Task", priority=5, estimated_duration=None)
        self.assertIsNone(task.estimated_duration)

    def test_from_dict_validates_empty_name(self):
        """Test that from_dict raises error for empty name."""
        data = {
            "id": 1,
            "name": "",  # Invalid name
            "priority": 5,
            "status": "PENDING",
        }
        with self.assertRaises(TaskValidationError) as context:
            Task.from_dict(data)
        self.assertIn("Task name cannot be empty", str(context.exception))

    def test_from_dict_with_valid_data(self):
        """Test that from_dict works with valid data."""
        data = {
            "id": 1,
            "name": "Test Task",
            "priority": 5,
            "status": "PENDING",
            "estimated_duration": 10.0,
        }
        task = Task.from_dict(data)
        self.assertEqual(task.id, 1)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, 5)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.estimated_duration, 10.0)

    def test_from_dict_raises_validation_errors(self):
        """Test that from_dict raises validation errors for various invalid fields."""
        test_cases = [
            (
                {"id": 1, "name": "Test Task", "priority": 0, "status": "PENDING"},
                "Priority must be greater than 0",
                "zero priority",
            ),
            (
                {"id": 1, "name": "Test Task", "priority": -100, "status": "PENDING"},
                "Priority must be greater than 0",
                "negative priority",
            ),
            (
                {
                    "id": 1,
                    "name": "Test Task",
                    "priority": 5,
                    "status": "PENDING",
                    "estimated_duration": 0.0,
                },
                "Estimated duration must be greater than 0",
                "zero estimated_duration",
            ),
            (
                {
                    "id": 1,
                    "name": "Test Task",
                    "priority": 5,
                    "status": "PENDING",
                    "estimated_duration": -5.0,
                },
                "Estimated duration must be greater than 0",
                "negative estimated_duration",
            ),
        ]
        for data, expected_error, description in test_cases:
            with self.subTest(description=description):
                with self.assertRaises(TaskValidationError) as context:
                    Task.from_dict(data)
                self.assertIn(expected_error, str(context.exception))


if __name__ == "__main__":
    unittest.main()
