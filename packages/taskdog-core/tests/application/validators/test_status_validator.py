"""Tests for StatusValidator."""

import unittest
from unittest.mock import Mock

from parameterized import parameterized

from taskdog_core.application.validators.status_validator import StatusValidator
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    DependencyNotMetError,
    TaskAlreadyFinishedError,
    TaskNotStartedError,
    TaskValidationError,
)


class TestStatusValidator(unittest.TestCase):
    """Test cases for StatusValidator."""

    def setUp(self):
        """Initialize validator and mock repository for each test."""
        self.validator = StatusValidator()
        self.mock_repository = Mock()

    @parameterized.expand(
        [
            ("pending_to_in_progress", TaskStatus.PENDING, TaskStatus.IN_PROGRESS),
            ("in_progress_to_completed", TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED),
            ("in_progress_to_pending", TaskStatus.IN_PROGRESS, TaskStatus.PENDING),
        ]
    )
    def test_validate_successful_status_transitions(
        self, scenario, current_status, target_status
    ):
        """Test valid status transitions."""
        task = Task(id=1, name="Test", status=current_status, priority=1)
        # Should not raise
        self.validator.validate(target_status, task, self.mock_repository)

    def test_validate_pending_to_completed_raises_error(self):
        """Test that PENDING task cannot transition directly to COMPLETED."""
        task = Task(id=1, name="Test", status=TaskStatus.PENDING, priority=1)

        with self.assertRaises(TaskNotStartedError) as context:
            self.validator.validate(TaskStatus.COMPLETED, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 1)

    @parameterized.expand(
        [
            ("completed_to_in_progress", TaskStatus.COMPLETED, TaskStatus.IN_PROGRESS),
            ("canceled_to_in_progress", TaskStatus.CANCELED, TaskStatus.IN_PROGRESS),
            ("completed_to_pending", TaskStatus.COMPLETED, TaskStatus.PENDING),
            ("canceled_to_completed", TaskStatus.CANCELED, TaskStatus.COMPLETED),
        ]
    )
    def test_validate_finished_task_transitions_raise_error(
        self, scenario, current_status, target_status
    ):
        """Test that finished tasks cannot transition to active states."""
        task = Task(id=1, name="Test", status=current_status, priority=1)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.validator.validate(target_status, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 1)
        self.assertEqual(context.exception.status, current_status.name)

    def test_validate_start_with_completed_dependencies_success(self):
        """Test that task with COMPLETED dependencies can be started."""
        task = Task(
            id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2]
        )

        # Mock repository to return completed dependencies
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.COMPLETED, priority=1)
        self.mock_repository.get_by_ids.return_value = {1: dep1, 2: dep2}

        # Should not raise
        self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

    @parameterized.expand(
        [
            ("pending_dependency", TaskStatus.PENDING),
            ("in_progress_dependency", TaskStatus.IN_PROGRESS),
        ]
    )
    def test_validate_start_with_unmet_dependency_raises_error(
        self, scenario, dep_status
    ):
        """Test that task with unmet dependencies cannot be started."""
        task = Task(
            id=2,
            name="Test",
            status=TaskStatus.PENDING,
            priority=1,
            depends_on=[1],
        )

        # Mock repository to return dependency with given status
        dep = Task(id=1, name="Dependency", status=dep_status, priority=1)
        self.mock_repository.get_by_ids.return_value = {1: dep}

        with self.assertRaises(DependencyNotMetError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(1, context.exception.unmet_dependencies)

    def test_validate_start_with_missing_dependency_raises_error(self):
        """Test that task with missing dependency cannot be started."""
        task = Task(
            id=2, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[999]
        )

        # Mock repository to return empty dict (dependency not found)
        self.mock_repository.get_by_ids.return_value = {}

        with self.assertRaises(DependencyNotMetError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 2)
        self.assertIn(999, context.exception.unmet_dependencies)

    def test_validate_start_with_mixed_dependencies_raises_error(self):
        """Test that task with mix of met and unmet dependencies cannot be started."""
        task = Task(
            id=3, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[1, 2]
        )

        # Mock repository: dep1 completed, dep2 pending
        dep1 = Task(id=1, name="Dep 1", status=TaskStatus.COMPLETED, priority=1)
        dep2 = Task(id=2, name="Dep 2", status=TaskStatus.PENDING, priority=1)
        self.mock_repository.get_by_ids.return_value = {1: dep1, 2: dep2}

        with self.assertRaises(DependencyNotMetError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertEqual(context.exception.task_id, 3)
        self.assertIn(2, context.exception.unmet_dependencies)
        self.assertNotIn(1, context.exception.unmet_dependencies)

    def test_validate_start_with_no_dependencies_success(self):
        """Test that task with no dependencies can be started."""
        task = Task(
            id=1, name="Test", status=TaskStatus.PENDING, priority=1, depends_on=[]
        )

        # Should not raise
        self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

    def test_validate_task_without_id_raises_error(self):
        """Test that task without ID raises TaskValidationError."""
        # Create task without ID (id=None)
        task = Task(name="Test", status=TaskStatus.PENDING, priority=1)

        with self.assertRaises(TaskValidationError) as context:
            self.validator.validate(TaskStatus.IN_PROGRESS, task, self.mock_repository)

        self.assertIn("Task ID must not be None", str(context.exception))

    @parameterized.expand(
        [
            ("pending_can_be_canceled", TaskStatus.PENDING, None),
            ("in_progress_can_be_canceled", TaskStatus.IN_PROGRESS, None),
            (
                "completed_cannot_be_canceled",
                TaskStatus.COMPLETED,
                TaskAlreadyFinishedError,
            ),
        ]
    )
    def test_validate_cancel_transitions(
        self, scenario, current_status, expected_error
    ):
        """Test cancel transitions for different task states."""
        task = Task(id=1, name="Test", status=current_status, priority=1)

        if expected_error:
            with self.assertRaises(expected_error) as context:
                self.validator.validate(TaskStatus.CANCELED, task, self.mock_repository)
            self.assertEqual(context.exception.task_id, 1)
            self.assertEqual(context.exception.status, current_status.name)
        else:
            # Should not raise
            self.validator.validate(TaskStatus.CANCELED, task, self.mock_repository)


if __name__ == "__main__":
    unittest.main()
