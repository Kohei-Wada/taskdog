"""Tests for StatusValidator."""

import unittest
from unittest.mock import Mock

from application.validators.status_validator import StatusValidator
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotStartedError,
)


class TestStatusValidator(unittest.TestCase):
    """Test cases for StatusValidator."""

    def setUp(self):
        """Initialize validator and mock repository for each test."""
        self.validator = StatusValidator()
        self.mock_repository = Mock()

    def test_validate_pending_to_in_progress_success(self):
        """Test that PENDING task can transition to IN_PROGRESS."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        # Should not raise
        self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

    def test_validate_in_progress_to_completed_success(self):
        """Test that IN_PROGRESS task can transition to COMPLETED."""
        task = Task(id=1, name="Test", status=TaskStatus.IN_PROGRESS, priority=1)

        # Should not raise
        self.validator.validate(TaskStatus.COMPLETED, task, self.mock_repository)

    def test_validate_in_progress_to_pending_success(self):
        """Test that IN_PROGRESS task can be paused to PENDING."""
        task = Task(id=1, name="Test", status=TaskStatus.IN_PROGRESS, priority=1)

        # Should not raise
        self.validator.validate(TaskStatus.PENDING, task, self.mock_repository)

    def test_validate_pending_to_completed_raises_error(self):
        """Test that PENDING task cannot transition directly to COMPLETED."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        with self.assertRaises(TaskNotStartedError) as context:
            self.validator.validate(TaskStatus.COMPLETED, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 1)

    def test_validate_completed_to_in_progress_raises_error(self):
        """Test that COMPLETED task cannot be restarted."""
        task = Task(id=1, name="Test", status=TaskStatus.COMPLETED, priority=1)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 1)
        self.assertEqual(context.exception.status, "COMPLETED")

    def test_validate_canceled_to_in_progress_raises_error(self):
        """Test that CANCELED task cannot be restarted."""
        task = Task(id=1, name="Test", status=TaskStatus.CANCELED, priority=1)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 1)
        self.assertEqual(context.exception.status, "CANCELED")

    def test_validate_completed_to_pending_raises_error(self):
        """Test that COMPLETED task cannot be paused."""
        task = Task(id=1, name="Test", status=TaskStatus.COMPLETED, priority=1)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.validator.validate(TaskStatus.PENDING, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 1)
        self.assertEqual(context.exception.status, "COMPLETED")

    def test_validate_canceled_to_completed_raises_error(self):
        """Test that CANCELED task cannot transition to COMPLETED."""
        task = Task(id=1, name="Test", status=TaskStatus.CANCELED, priority=1)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.validator.validate(TaskStatus.COMPLETED, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 1)
        self.assertEqual(context.exception.status, "CANCELED")


if __name__ == "__main__":
    unittest.main()
