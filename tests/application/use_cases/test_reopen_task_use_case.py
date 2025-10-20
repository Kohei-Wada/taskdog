"""Tests for ReopenTaskUseCase."""

import os
import tempfile
import unittest

from application.dto.reopen_task_input import ReopenTaskInput
from application.use_cases.reopen_task import ReopenTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import (
    DependencyNotMetError,
    TaskNotFoundException,
    TaskValidationError,
)
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestReopenTaskUseCase(unittest.TestCase):
    """Test cases for ReopenTaskUseCase."""

    def setUp(self):
        """Create temporary file and initialize use case for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = ReopenTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_reopens_completed_task(self):
        """Test execute reopens a completed task."""
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start="2025-01-01 09:00:00",
            actual_end="2025-01-01 12:00:00",
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertIsNone(result.actual_start)
        self.assertIsNone(result.actual_end)

    def test_execute_reopens_canceled_task(self):
        """Test execute reopens a canceled task."""
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.CANCELED,
            actual_end="2025-01-01 12:00:00",
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertIsNone(result.actual_end)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start="2025-01-01 09:00:00",
            actual_end="2025-01-01 12:00:00",
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.PENDING)
        self.assertIsNone(retrieved.actual_start)
        self.assertIsNone(retrieved.actual_end)

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = ReopenTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_with_pending_task_raises_error(self):
        """Test execute with PENDING task raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.PENDING)

        input_dto = ReopenTaskInput(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Cannot reopen task with status PENDING", str(context.exception))

    def test_execute_with_in_progress_task_raises_error(self):
        """Test execute with IN_PROGRESS task raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)

        input_dto = ReopenTaskInput(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Cannot reopen task with status IN_PROGRESS", str(context.exception))

    def test_execute_with_deleted_task_raises_error(self):
        """Test execute with deleted task raises TaskValidationError."""
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.COMPLETED, is_deleted=True
        )

        input_dto = ReopenTaskInput(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Cannot reopen deleted task", str(context.exception))

    def test_execute_with_met_dependencies_succeeds(self):
        """Test execute with completed dependencies succeeds."""
        # Create dependency tasks (completed)
        dep1 = self.repository.create(name="Dep 1", priority=1, status=TaskStatus.COMPLETED)
        dep2 = self.repository.create(name="Dep 2", priority=1, status=TaskStatus.COMPLETED)

        # Create completed task with dependencies
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[dep1.id, dep2.id],
        )

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_execute_with_unmet_dependencies_raises_error(self):
        """Test execute with unmet dependencies raises DependencyNotMetError."""
        # Create dependency (not completed)
        dep = self.repository.create(name="Dependency", priority=1, status=TaskStatus.PENDING)

        # Create completed task depending on pending task
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[dep.id],
        )

        input_dto = ReopenTaskInput(task_id=task.id)

        with self.assertRaises(DependencyNotMetError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("dependencies not met", str(context.exception))
        self.assertIn(str(dep.id), str(context.exception))

    def test_execute_with_missing_dependency_raises_error(self):
        """Test execute with missing dependency raises DependencyNotMetError."""
        # Create completed task with non-existent dependency
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[999],  # Non-existent task
        )

        input_dto = ReopenTaskInput(task_id=task.id)

        with self.assertRaises(DependencyNotMetError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("dependencies not met", str(context.exception))
        self.assertIn("999", str(context.exception))

    def test_execute_with_mixed_dependencies_raises_error(self):
        """Test execute with mix of met and unmet dependencies raises error."""
        # Create one completed and one pending dependency
        dep1 = self.repository.create(name="Dep 1", priority=1, status=TaskStatus.COMPLETED)
        dep2 = self.repository.create(name="Dep 2", priority=1, status=TaskStatus.PENDING)

        # Create completed task
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[dep1.id, dep2.id],
        )

        input_dto = ReopenTaskInput(task_id=task.id)

        with self.assertRaises(DependencyNotMetError) as context:
            self.use_case.execute(input_dto)

        # Should mention the unmet dependency
        self.assertIn(str(dep2.id), str(context.exception))

    def test_execute_with_no_dependencies_succeeds(self):
        """Test execute with no dependencies succeeds."""
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.COMPLETED)

        input_dto = ReopenTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
