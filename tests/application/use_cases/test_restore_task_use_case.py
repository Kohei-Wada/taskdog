"""Tests for RestoreTaskUseCase."""

import os
import tempfile
import unittest

from application.dto.restore_task_request import RestoreTaskRequest
from application.use_cases.restore_task import RestoreTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestRestoreTaskUseCase(unittest.TestCase):
    """Test cases for RestoreTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = RestoreTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_restores_archived_task(self):
        """Test execute changes ARCHIVED status to PENDING"""
        # Create an archived task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.ARCHIVED)

        input_dto = RestoreTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        # Create an archived task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.ARCHIVED)

        input_dto = RestoreTaskRequest(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.PENDING)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = RestoreTaskRequest(task_id=999)

        with self.assertRaises(TaskNotFoundException):
            self.use_case.execute(input_dto)

    def test_execute_cannot_restore_non_archived_task(self):
        """Test execute with non-archived task raises ValidationError"""
        # Create a completed (but not archived) task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.COMPLETED)

        input_dto = RestoreTaskRequest(task_id=task.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Only ARCHIVED", str(context.exception))

    def test_execute_preserves_other_fields(self):
        """Test execute only modifies status field"""
        # Create archived task with various fields
        task = self.repository.create(
            name="Test Task",
            priority=5,
            status=TaskStatus.ARCHIVED,
            estimated_duration=8.0,
        )
        original_name = task.name
        original_priority = task.priority
        original_duration = task.estimated_duration

        input_dto = RestoreTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify only status changed
        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertEqual(result.name, original_name)
        self.assertEqual(result.priority, original_priority)
        self.assertEqual(result.estimated_duration, original_duration)


if __name__ == "__main__":
    unittest.main()
