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

    def test_empty_name_raises_error(self):
        """Test that empty task name raises TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="", priority=5)
        self.assertIn("Task name cannot be empty", str(context.exception))

    def test_whitespace_only_name_raises_error(self):
        """Test that whitespace-only task name raises TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="   ", priority=5)
        self.assertIn("Task name cannot be empty", str(context.exception))

    def test_zero_priority_raises_error(self):
        """Test that priority = 0 raises TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="Test Task", priority=0)
        self.assertIn("Priority must be greater than 0", str(context.exception))

    def test_negative_priority_raises_error(self):
        """Test that negative priority raises TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="Test Task", priority=-1)
        self.assertIn("Priority must be greater than 0", str(context.exception))

    def test_zero_estimated_duration_raises_error(self):
        """Test that estimated_duration = 0 raises TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="Test Task", priority=5, estimated_duration=0.0)
        self.assertIn("Estimated duration must be greater than 0", str(context.exception))

    def test_negative_estimated_duration_raises_error(self):
        """Test that negative estimated_duration raises TaskValidationError."""
        with self.assertRaises(TaskValidationError) as context:
            Task(name="Test Task", priority=5, estimated_duration=-5.0)
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

    def test_from_dict_raises_error_for_zero_priority(self):
        """Test that from_dict raises error for priority = 0."""
        data = {
            "id": 1,
            "name": "Test Task",
            "priority": 0,  # Invalid priority
            "status": "PENDING",
        }
        with self.assertRaises(TaskValidationError) as context:
            Task.from_dict(data)
        self.assertIn("Priority must be greater than 0", str(context.exception))

    def test_from_dict_raises_error_for_negative_priority(self):
        """Test that from_dict raises error for negative priority."""
        data = {
            "id": 1,
            "name": "Test Task",
            "priority": -100,  # Invalid priority
            "status": "PENDING",
        }
        with self.assertRaises(TaskValidationError) as context:
            Task.from_dict(data)
        self.assertIn("Priority must be greater than 0", str(context.exception))

    def test_from_dict_raises_error_for_zero_estimated_duration(self):
        """Test that from_dict raises error for estimated_duration = 0."""
        data = {
            "id": 1,
            "name": "Test Task",
            "priority": 5,
            "status": "PENDING",
            "estimated_duration": 0.0,  # Invalid duration
        }
        with self.assertRaises(TaskValidationError) as context:
            Task.from_dict(data)
        self.assertIn("Estimated duration must be greater than 0", str(context.exception))

    def test_from_dict_raises_error_for_negative_estimated_duration(self):
        """Test that from_dict raises error for negative estimated_duration."""
        data = {
            "id": 1,
            "name": "Test Task",
            "priority": 5,
            "status": "PENDING",
            "estimated_duration": -5.0,  # Invalid duration
        }
        with self.assertRaises(TaskValidationError) as context:
            Task.from_dict(data)
        self.assertIn("Estimated duration must be greater than 0", str(context.exception))


if __name__ == "__main__":
    unittest.main()
