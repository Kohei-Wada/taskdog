"""Tests for DependencyValidator."""

import unittest
from unittest.mock import Mock

from application.validators.dependency_validator import DependencyValidator
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import DependencyNotMetError


class TestDependencyValidator(unittest.TestCase):
    """Test cases for DependencyValidator."""

    def setUp(self):
        """Initialize mock repository for each test."""
        self.mock_repository = Mock()

    def test_validate_dependencies_met_with_no_dependencies(self):
        """Test that task with no dependencies passes validation."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[])

        # Should not raise
        DependencyValidator.validate_dependencies_met(task, self.mock_repository)

    def test_validate_dependencies_met_with_completed_dependencies(self):
        """Test that task with all COMPLETED dependencies passes validation."""
        task = Task(id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2])

        # Mock repository to return completed dependencies
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.COMPLETED, priority=1)
        self.mock_repository.get_by_id.side_effect = lambda id: dep1 if id == 1 else dep2

        # Should not raise
        DependencyValidator.validate_dependencies_met(task, self.mock_repository)

    def test_validate_dependencies_met_with_pending_dependency_raises_error(self):
        """Test that task with PENDING dependency fails validation."""
        task = Task(id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1])

        # Mock repository to return pending dependency
        dep = Task(id=1, name="Dependency", status=TaskStatus.PENDING, priority=1)
        self.mock_repository.get_by_id.return_value = dep

        with self.assertRaises(DependencyNotMetError) as context:
            DependencyValidator.validate_dependencies_met(task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(1, context.exception.unmet_dependencies)

    def test_validate_dependencies_met_with_in_progress_dependency_raises_error(self):
        """Test that task with IN_PROGRESS dependency fails validation."""
        task = Task(id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1])

        # Mock repository to return in-progress dependency
        dep = Task(id=1, name="Dependency", status=TaskStatus.IN_PROGRESS, priority=1)
        self.mock_repository.get_by_id.return_value = dep

        with self.assertRaises(DependencyNotMetError) as context:
            DependencyValidator.validate_dependencies_met(task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(1, context.exception.unmet_dependencies)

    def test_validate_dependencies_met_with_canceled_dependency_raises_error(self):
        """Test that task with CANCELED dependency fails validation."""
        task = Task(id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1])

        # Mock repository to return canceled dependency
        dep = Task(id=1, name="Dependency", status=TaskStatus.CANCELED, priority=1)
        self.mock_repository.get_by_id.return_value = dep

        with self.assertRaises(DependencyNotMetError) as context:
            DependencyValidator.validate_dependencies_met(task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(1, context.exception.unmet_dependencies)

    def test_validate_dependencies_met_with_missing_dependency_raises_error(self):
        """Test that task with missing dependency fails validation."""
        task = Task(id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[999])

        # Mock repository to return None (dependency not found)
        self.mock_repository.get_by_id.return_value = None

        with self.assertRaises(DependencyNotMetError) as context:
            DependencyValidator.validate_dependencies_met(task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(999, context.exception.unmet_dependencies)

    def test_validate_dependencies_met_with_mixed_dependencies_raises_error(self):
        """Test that task with mix of met and unmet dependencies fails validation."""
        task = Task(id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2])

        # Mock repository: dep1 completed, dep2 pending
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.PENDING, priority=1)
        self.mock_repository.get_by_id.side_effect = lambda id: dep1 if id == 1 else dep2

        with self.assertRaises(DependencyNotMetError) as context:
            DependencyValidator.validate_dependencies_met(task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 3)
        # Only unmet dependency should be in the list
        self.assertIn(2, context.exception.unmet_dependencies)
        self.assertNotIn(1, context.exception.unmet_dependencies)

    def test_validate_dependencies_met_with_multiple_unmet_dependencies(self):
        """Test that all unmet dependencies are collected."""
        task = Task(id=4, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2, 3])

        # Mock repository: all dependencies are pending
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.PENDING, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.IN_PROGRESS, priority=1)
        dep3 = Task(id=3, name="Dep 3", status=TaskStatus.CANCELED, priority=1)
        self.mock_repository.get_by_id.side_effect = lambda id: (
            dep1 if id == 1 else dep2 if id == 2 else dep3
        )

        with self.assertRaises(DependencyNotMetError) as context:
            DependencyValidator.validate_dependencies_met(task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 4)
        # All three dependencies should be unmet
        self.assertEqual(len(context.exception.unmet_dependencies), 3)
        self.assertIn(1, context.exception.unmet_dependencies)
        self.assertIn(2, context.exception.unmet_dependencies)
        self.assertIn(3, context.exception.unmet_dependencies)


if __name__ == "__main__":
    unittest.main()
