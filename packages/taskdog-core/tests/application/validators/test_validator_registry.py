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
