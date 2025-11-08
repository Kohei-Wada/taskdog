"""Tests for RestoreTaskUseCase."""

import os
import tempfile
import unittest

from taskdog_core.application.dto.restore_task_input import RestoreTaskInput
from taskdog_core.application.use_cases.restore_task import RestoreTaskUseCase
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestRestoreTaskUseCase(unittest.TestCase):
    """Test cases for RestoreTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".db"
        )
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = SqliteTaskRepository(f"sqlite:///{self.test_filename}")
        self.use_case = RestoreTaskUseCase(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if hasattr(self, "repository") and hasattr(self.repository, "close"):
            self.repository.close()
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_restores_archived_task(self):
        """Test execute clears is_archived flag and preserves status"""
        # Create an archived task (PENDING + is_archived)
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )
        task.is_archived = True
        self.repository.save(task)

        input_dto = RestoreTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertFalse(result.is_archived)
        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        # Create an archived task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )
        task.is_archived = True
        self.repository.save(task)

        input_dto = RestoreTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        self.assertFalse(retrieved.is_archived)
        self.assertEqual(retrieved.status, TaskStatus.PENDING)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = RestoreTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException):
            self.use_case.execute(input_dto)

    def test_execute_cannot_restore_non_archived_task(self):
        """Test execute with non-archived task raises ValidationError"""
        # Create a completed (but not archived) task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.COMPLETED
        )

        input_dto = RestoreTaskInput(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Only archived", str(context.exception))

    def test_execute_preserves_other_fields(self):
        """Test execute only modifies is_archived flag"""
        # Create archived task with various fields
        task = self.repository.create(
            name="Test Task",
            priority=5,
            status=TaskStatus.PENDING,
            estimated_duration=8.0,
        )
        task.is_archived = True
        self.repository.save(task)

        original_name = task.name
        original_priority = task.priority
        original_duration = task.estimated_duration
        original_status = task.status

        input_dto = RestoreTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify only is_archived changed
        self.assertFalse(result.is_archived)
        self.assertEqual(result.status, original_status)
        self.assertEqual(result.name, original_name)
        self.assertEqual(result.priority, original_priority)
        self.assertEqual(result.estimated_duration, original_duration)

    def test_execute_restores_archived_completed_task(self):
        """Test execute restores archived COMPLETED task with original status"""
        # Create an archived completed task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.COMPLETED
        )
        task.is_archived = True
        self.repository.save(task)

        input_dto = RestoreTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify archived flag cleared and status preserved
        self.assertFalse(result.is_archived)
        self.assertEqual(result.status, TaskStatus.COMPLETED)

    def test_execute_restores_archived_canceled_task(self):
        """Test execute restores archived CANCELED task with original status"""
        # Create an archived canceled task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.CANCELED
        )
        task.is_archived = True
        self.repository.save(task)

        input_dto = RestoreTaskInput(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify archived flag cleared and status preserved
        self.assertFalse(result.is_archived)
        self.assertEqual(result.status, TaskStatus.CANCELED)


if __name__ == "__main__":
    unittest.main()
