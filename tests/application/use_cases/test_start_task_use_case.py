import contextlib
import os
import tempfile
import unittest

from application.dto.start_task_request import StartTaskRequest
from application.use_cases.start_task import StartTaskUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
)
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestStartTaskUseCase(unittest.TestCase):
    """Test cases for StartTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = StartTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_sets_status_to_in_progress(self):
        """Test execute sets task status to IN_PROGRESS"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)

    def test_execute_records_actual_start_time(self):
        """Test execute records actual start timestamp"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNotNone(result.actual_start)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskRequest(task_id=task.id)
        self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(retrieved.actual_start)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = StartTaskRequest(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_does_not_update_actual_end(self):
        """Test execute does not set actual_end when starting"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNone(result.actual_end)

    def test_execute_without_parent_works_normally(self):
        """Test execute works normally for tasks without parent"""
        task = Task(name="Test Task", priority=1)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = StartTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(result.actual_start)

    def test_execute_raises_error_when_starting_completed_task(self):
        """Test execute raises TaskAlreadyFinishedError when starting COMPLETED task"""
        # Create and complete a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        task.actual_start = "2024-01-01 10:00:00"
        task.actual_end = "2024-01-01 12:00:00"
        self.repository.save(task)

        # Try to start the completed task - should raise error
        input_dto = StartTaskRequest(task_id=task.id)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.use_case.execute(input_dto)

        # Verify error details
        self.assertEqual(context.exception.task_id, task.id)
        self.assertEqual(context.exception.status, TaskStatus.COMPLETED.value)

    def test_execute_raises_error_when_starting_canceled_task(self):
        """Test execute raises TaskAlreadyFinishedError when starting CANCELED task"""
        # Create a canceled task
        task = Task(name="Test Task", priority=1, status=TaskStatus.CANCELED)
        task.id = self.repository.generate_next_id()
        task.actual_start = "2024-01-01 10:00:00"
        task.actual_end = "2024-01-01 11:00:00"
        self.repository.save(task)

        # Try to start the canceled task - should raise error
        input_dto = StartTaskRequest(task_id=task.id)

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

        # Try to start the completed task
        input_dto = StartTaskRequest(task_id=task.id)

        with contextlib.suppress(TaskAlreadyFinishedError):
            self.use_case.execute(input_dto)

        # Verify task state remains unchanged
        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.COMPLETED)
        self.assertEqual(retrieved.actual_start, "2024-01-01 10:00:00")
        self.assertEqual(retrieved.actual_end, "2024-01-01 12:00:00")


if __name__ == "__main__":
    unittest.main()
