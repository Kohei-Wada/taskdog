"""Tests for TaskFieldValidatorRegistry."""

import unittest
from unittest.mock import Mock

from application.validators.validator_registry import TaskFieldValidatorRegistry
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskNotStartedError


class TestTaskFieldValidatorRegistry(unittest.TestCase):
    """Test cases for TaskFieldValidatorRegistry."""

    def setUp(self):
        """Initialize registry with mock repository for each test."""
        self.mock_repository = Mock()
        self.registry = TaskFieldValidatorRegistry(self.mock_repository)

    def test_init_registers_status_validator(self):
        """Test that status validator is registered on initialization."""
        self.assertTrue(self.registry.has_validator("status"))

    def test_has_validator_returns_true_for_registered_field(self):
        """Test has_validator returns True for registered field."""
        self.assertTrue(self.registry.has_validator("status"))

    def test_has_validator_returns_false_for_unregistered_field(self):
        """Test has_validator returns False for unregistered field."""
        self.assertFalse(self.registry.has_validator("name"))
        self.assertFalse(self.registry.has_validator("priority"))
        self.assertFalse(self.registry.has_validator("deadline"))

    def test_validate_field_calls_status_validator(self):
        """Test validate_field calls status validator for status field."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        # Should not raise for valid transition
        self.registry.validate_field("status", TaskStatus.IN_PROGRESS, task)

    def test_validate_field_raises_error_for_invalid_status_transition(self):
        """Test validate_field raises error for invalid status transition."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        # Should raise for invalid transition (PENDING -> COMPLETED)
        with self.assertRaises(TaskNotStartedError):
            self.registry.validate_field("status", TaskStatus.COMPLETED, task)

    def test_validate_field_does_nothing_for_unregistered_field(self):
        """Test validate_field does nothing for fields without validators."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        # Should not raise even with invalid values for unregistered fields
        self.registry.validate_field("name", "", task)
        self.registry.validate_field("priority", -999, task)
        self.registry.validate_field("unknown_field", None, task)

    def test_registry_stores_repository_reference(self):
        """Test that registry stores repository reference for validators."""
        self.assertIs(self.registry.repository, self.mock_repository)


if __name__ == "__main__":
    unittest.main()
