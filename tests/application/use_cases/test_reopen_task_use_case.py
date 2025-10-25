"""Tests for ReopenTaskUseCase."""

import os
import tempfile
import unittest
from datetime import datetime

from application.dto.reopen_task_request import ReopenTaskRequest
from application.use_cases.reopen_task import ReopenTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import (
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
            actual_start=datetime(2025, 1, 1, 9, 0, 0),
            actual_end=datetime(2025, 1, 1, 12, 0, 0),
        )

        input_dto = ReopenTaskRequest(task_id=task.id)
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
            actual_end=datetime(2025, 1, 1, 12, 0, 0),
        )

        input_dto = ReopenTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertIsNone(result.actual_end)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            actual_start=datetime(2025, 1, 1, 9, 0, 0),
            actual_end=datetime(2025, 1, 1, 12, 0, 0),
        )

        input_dto = ReopenTaskRequest(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.PENDING)
        self.assertIsNone(retrieved.actual_start)
        self.assertIsNone(retrieved.actual_end)

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = ReopenTaskRequest(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_with_pending_task_raises_error(self):
        """Test execute with PENDING task raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.PENDING)

        input_dto = ReopenTaskRequest(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Cannot reopen task with status PENDING", str(context.exception))

    def test_execute_with_in_progress_task_raises_error(self):
        """Test execute with IN_PROGRESS task raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)

        input_dto = ReopenTaskRequest(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Cannot reopen task with status IN_PROGRESS", str(context.exception))

    def test_execute_with_archived_task_raises_error(self):
        """Test execute with archived task raises TaskValidationError."""
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.ARCHIVED)

        input_dto = ReopenTaskRequest(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Cannot reopen task with status ARCHIVED", str(context.exception))
        self.assertIn("Use 'restore' command", str(context.exception))

    def test_execute_with_dependencies_always_succeeds(self):
        """Test that reopen succeeds regardless of dependency states.

        Dependencies are NOT validated during reopen. This allows flexible
        restoration of task states. Dependency validation will occur when
        attempting to start the task.
        """
        # Create dependency (not completed)
        dep = self.repository.create(name="Dependency", priority=1, status=TaskStatus.PENDING)

        # Create completed task depending on pending task
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[dep.id],
        )

        input_dto = ReopenTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Should succeed even though dependency is not completed
        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_execute_with_missing_dependency_succeeds(self):
        """Test that reopen succeeds even with missing dependencies."""
        # Create completed task with non-existent dependency
        task = self.repository.create(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            depends_on=[999],  # Non-existent task
        )

        input_dto = ReopenTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Should succeed even though dependency doesn't exist
        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_execute_with_no_dependencies_succeeds(self):
        """Test execute with no dependencies succeeds."""
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.COMPLETED)

        input_dto = ReopenTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
