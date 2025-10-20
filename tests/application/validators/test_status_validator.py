"""Tests for StatusValidator."""

import unittest
from unittest.mock import Mock

from application.validators.status_validator import StatusValidator
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    DependencyNotMetError,
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

    def test_validate_start_with_completed_dependencies_success(self):
        """Test that task with COMPLETED dependencies can be started."""
        task = Task(id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2])

        # Mock repository to return completed dependencies
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.COMPLETED, priority=1)
        self.mock_repository.get_by_id.side_effect = lambda id: dep1 if id == 1 else dep2

        # Should not raise
        self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

    def test_validate_start_with_pending_dependency_raises_error(self):
        """Test that task with PENDING dependency cannot be started."""
        task = Task(id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1])

        # Mock repository to return pending dependency
        dep = Task(id=1, name="Dependency", status=TaskStatus.PENDING, priority=1)
        self.mock_repository.get_by_id.return_value = dep

        with self.assertRaises(DependencyNotMetError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(1, context.exception.unmet_dependencies)

    def test_validate_start_with_in_progress_dependency_raises_error(self):
        """Test that task with IN_PROGRESS dependency cannot be started."""
        task = Task(id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1])

        # Mock repository to return in-progress dependency
        dep = Task(id=1, name="Dependency", status=TaskStatus.IN_PROGRESS, priority=1)
        self.mock_repository.get_by_id.return_value = dep

        with self.assertRaises(DependencyNotMetError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(1, context.exception.unmet_dependencies)

    def test_validate_start_with_missing_dependency_raises_error(self):
        """Test that task with missing dependency cannot be started."""
        task = Task(id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[999])

        # Mock repository to return None (dependency not found)
        self.mock_repository.get_by_id.return_value = None

        with self.assertRaises(DependencyNotMetError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(999, context.exception.unmet_dependencies)

    def test_validate_start_with_mixed_dependencies_raises_error(self):
        """Test that task with mix of met and unmet dependencies cannot be started."""
        task = Task(id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2])

        # Mock repository: dep1 completed, dep2 pending
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.PENDING, priority=1)
        self.mock_repository.get_by_id.side_effect = lambda id: dep1 if id == 1 else dep2

        with self.assertRaises(DependencyNotMetError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 3)
        self.assertIn(2, context.exception.unmet_dependencies)
        self.assertNotIn(1, context.exception.unmet_dependencies)

    def test_validate_start_with_no_dependencies_success(self):
        """Test that task with no dependencies can be started."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[])

        # Should not raise
        self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)


if __name__ == "__main__":
    unittest.main()
