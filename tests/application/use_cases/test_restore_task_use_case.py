"""Tests for RestoreTaskUseCase."""

import os
import tempfile
import unittest

from application.dto.restore_task_request import RestoreTaskRequest
from application.use_cases.restore_task import RestoreTaskUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestRestoreTaskUseCase(unittest.TestCase):
    """Test cases for RestoreTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.use_case = RestoreTaskUseCase(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_restores_deleted_task(self):
        """Test execute clears is_deleted flag"""
        # Create an archived (deleted) task
        task = Task(name="Test Task", priority=1, is_deleted=True)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)
        self.assertTrue(task.is_deleted)

        input_dto = RestoreTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertFalse(result.is_deleted)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        # Create an archived task
        task = Task(name="Test Task", priority=1, is_deleted=True)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = RestoreTaskRequest(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task.id)
        self.assertFalse(retrieved.is_deleted)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = RestoreTaskRequest(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_preserves_task_status(self):
        """Test execute does not modify task status"""
        # Create archived task with COMPLETED status
        task = Task(
            name="Test Task",
            priority=1,
            status=TaskStatus.COMPLETED,
            is_deleted=True,
            actual_start="2024-01-01 10:00:00",
            actual_end="2024-01-01 12:00:00",
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = RestoreTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Status should remain COMPLETED
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertFalse(result.is_deleted)

    def test_execute_preserves_all_task_fields(self):
        """Test execute only modifies is_deleted flag"""
        # Create archived task with various fields
        task = Task(
            name="Test Task",
            priority=5,
            status=TaskStatus.CANCELED,
            is_deleted=True,
            planned_start="2025-01-01 09:00:00",
            planned_end="2025-01-01 18:00:00",
            deadline="2025-01-02 18:00:00",
            estimated_duration=8.0,
            actual_start="2025-01-01 09:00:00",
            actual_end="2025-01-01 12:00:00",
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = RestoreTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify all fields preserved except is_deleted
        self.assertFalse(result.is_deleted)
        self.assertEqual(result.name, "Test Task")
        self.assertEqual(result.priority, 5)
        self.assertEqual(result.status, TaskStatus.CANCELED)
        self.assertEqual(result.planned_start, "2025-01-01 09:00:00")
        self.assertEqual(result.planned_end, "2025-01-01 18:00:00")
        self.assertEqual(result.deadline, "2025-01-02 18:00:00")
        self.assertEqual(result.estimated_duration, 8.0)
        self.assertEqual(result.actual_start, "2025-01-01 09:00:00")
        self.assertEqual(result.actual_end, "2025-01-01 12:00:00")

    def test_execute_can_restore_already_active_task(self):
        """Test execute works on non-deleted tasks (idempotent)"""
        # Create a non-deleted task
        task = Task(name="Test Task", priority=1, is_deleted=False)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = RestoreTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Should remain not deleted
        self.assertFalse(result.is_deleted)


if __name__ == "__main__":
    unittest.main()
