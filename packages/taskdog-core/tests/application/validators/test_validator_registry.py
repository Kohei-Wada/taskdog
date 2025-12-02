"""Tests for TaskFieldValidatorRegistry."""

from unittest.mock import Mock

import pytest

from taskdog_core.application.validators.validator_registry import (
    TaskFieldValidatorRegistry,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import TaskNotStartedError


class TestTaskFieldValidatorRegistry:
    """Test cases for TaskFieldValidatorRegistry."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize registry with mock repository for each test."""
        self.mock_repository = Mock()
        self.registry = TaskFieldValidatorRegistry(self.mock_repository)

    def test_init_registers_status_validator(self):
        """Test that status validator is registered on initialization."""
        assert self.registry.has_validator("status") is True

    def test_init_registers_datetime_validators(self):
        """Test that datetime validators are registered on initialization."""
        assert self.registry.has_validator("deadline") is True
        assert self.registry.has_validator("planned_start") is True
        assert self.registry.has_validator("planned_end") is True

    def test_init_registers_numeric_validators(self):
        """Test that numeric validators are registered on initialization."""
        assert self.registry.has_validator("estimated_duration") is True
        assert self.registry.has_validator("priority") is True

    def test_has_validator_returns_true_for_registered_field(self):
        """Test has_validator returns True for registered field."""
        assert self.registry.has_validator("status") is True

    def test_has_validator_returns_false_for_unregistered_field(self):
        """Test has_validator returns False for unregistered field."""
        assert self.registry.has_validator("name") is False
        assert self.registry.has_validator("is_fixed") is False
        assert self.registry.has_validator("depends_on") is False

    def test_validate_field_calls_status_validator(self):
        """Test validate_field calls status validator for status field."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        # Should not raise for valid transition
        self.registry.validate_field("status", TaskStatus.IN_PROGRESS, task)

    def test_validate_field_raises_error_for_invalid_status_transition(self):
        """Test validate_field raises error for invalid status transition."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        # Should raise for invalid transition (PENDING -> COMPLETED)
        with pytest.raises(TaskNotStartedError):
            self.registry.validate_field("status", TaskStatus.COMPLETED, task)

    def test_validate_field_does_nothing_for_unregistered_field(self):
        """Test validate_field does nothing for fields without validators."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        # Should not raise even with invalid values for unregistered fields
        self.registry.validate_field("name", "", task)
        self.registry.validate_field("is_fixed", "invalid", task)
        self.registry.validate_field("unknown_field", None, task)

    def test_registry_stores_repository_reference(self):
        """Test that registry stores repository reference for validators."""
        assert self.registry.repository is self.mock_repository
