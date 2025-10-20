"""Tests for CancelTaskUseCase."""

import contextlib
import os
import tempfile
import unittest

from application.dto.cancel_task_request import CancelTaskRequest
from application.use_cases.cancel_task import CancelTaskUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
)
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestCancelTaskUseCase(unittest.TestCase):
    """Test cases for CancelTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = CancelTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_sets_status_to_canceled(self):
        """Test execute sets task status to CANCELED"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CancelTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.CANCELED)

    def test_execute_records_actual_end_time(self):
        """Test execute records actual end timestamp"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CancelTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNotNone(result.actual_end)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CancelTaskRequest(task_id=task.id)
        self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.CANCELED)
        self.assertIsNotNone(retrieved.actual_end)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = CancelTaskRequest(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_can_cancel_pending_task(self):
        """Test execute can cancel PENDING task"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = CancelTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.CANCELED)
        self.assertIsNotNone(result.actual_end)
        self.assertIsNone(result.actual_start)

    def test_execute_can_cancel_in_progress_task(self):
        """Test execute can cancel IN_PROGRESS task"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        task.actual_start = "2024-01-01 10:00:00"
        self.repository.save(task)

        input_dto = CancelTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.CANCELED)
        self.assertIsNotNone(result.actual_start)
        self.assertIsNotNone(result.actual_end)

    def test_execute_raises_error_when_canceling_completed_task(self):
        """Test execute raises TaskAlreadyFinishedError when canceling COMPLETED task"""
        # Create and complete a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        task.actual_start = "2024-01-01 10:00:00"
        task.actual_end = "2024-01-01 12:00:00"
        self.repository.save(task)

        # Try to cancel the completed task - should raise error
        input_dto = CancelTaskRequest(task_id=task.id)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.use_case.execute(input_dto)

        # Verify error details
        self.assertEqual(context.exception.task_id, task.id)
        self.assertEqual(context.exception.status, TaskStatus.COMPLETED.value)

    def test_execute_raises_error_when_canceling_already_canceled_task(self):
        """Test execute raises TaskAlreadyFinishedError when canceling already CANCELED task"""
        # Create a canceled task
        task = Task(name="Test Task", priority=1, status=TaskStatus.CANCELED)
        task.id = self.repository.generate_next_id()
        task.actual_end = "2024-01-01 11:00:00"
        self.repository.save(task)

        # Try to cancel the already canceled task - should raise error
        input_dto = CancelTaskRequest(task_id=task.id)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.use_case.execute(input_dto)

        # Verify error details
        self.assertEqual(context.exception.task_id, task.id)
        self.assertEqual(context.exception.status, TaskStatus.CANCELED.value)

    def test_execute_does_not_modify_completed_task_state(self):
        """Test execute does not modify state when attempted on COMPLETED task"""
        # Create and complete a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        task.actual_start = "2024-01-01 10:00:00"
        task.actual_end = "2024-01-01 12:00:00"
        self.repository.save(task)

        # Try to cancel the completed task
        input_dto = CancelTaskRequest(task_id=task.id)

        with contextlib.suppress(TaskAlreadyFinishedError):
            self.use_case.execute(input_dto)

        # Verify task state remains unchanged
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.COMPLETED)
        self.assertEqual(retrieved.actual_start, "2024-01-01 10:00:00")
        self.assertEqual(retrieved.actual_end, "2024-01-01 12:00:00")


if __name__ == "__main__":
    unittest.main()
