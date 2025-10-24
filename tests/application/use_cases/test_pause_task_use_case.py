import os
import tempfile
import unittest
from datetime import datetime

from application.dto.pause_task_request import PauseTaskRequest
from application.use_cases.pause_task import PauseTaskUseCase
from domain.entities.task import Task, TaskStatus
from domain.exceptions.task_exceptions import (
    TaskAlreadyFinishedError,
    TaskNotFoundException,
)
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestPauseTaskUseCase(unittest.TestCase):
    """Test cases for PauseTaskUseCase"""

    def setUp(self):
        """Create temporary file and initialize use case for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.use_case = PauseTaskUseCase(self.repository, self.time_tracker)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_sets_status_to_pending(self):
        """Test execute sets task status to PENDING"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        self.repository.save(task)

        input_dto = PauseTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_execute_clears_actual_start_time(self):
        """Test execute clears actual start timestamp"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        self.repository.save(task)

        input_dto = PauseTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNone(result.actual_start)

    def test_execute_clears_actual_end_time(self):
        """Test execute clears actual end timestamp if present"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        task.actual_end = datetime(2024, 1, 1, 12, 0, 0)  # Shouldn't normally exist for IN_PROGRESS
        self.repository.save(task)

        input_dto = PauseTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertIsNone(result.actual_end)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        self.repository.save(task)

        input_dto = PauseTaskRequest(task_id=task.id)
        self.use_case.execute(input_dto)

        retrieved = self.repository.get_by_id(task.id)
        self.assertEqual(retrieved.status, TaskStatus.PENDING)
        self.assertIsNone(retrieved.actual_start)
        self.assertIsNone(retrieved.actual_end)

    def test_execute_with_invalid_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException"""
        input_dto = PauseTaskRequest(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_with_pending_task_is_idempotent(self):
        """Test execute works correctly when task is already PENDING"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        input_dto = PauseTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertIsNone(result.actual_start)
        self.assertIsNone(result.actual_end)

    def test_execute_raises_error_when_pausing_completed_task(self):
        """Test execute raises TaskAlreadyFinishedError when pausing COMPLETED task"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        task.actual_end = datetime(2024, 1, 1, 12, 0, 0)
        self.repository.save(task)

        input_dto = PauseTaskRequest(task_id=task.id)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, task.id)
        self.assertEqual(context.exception.status, TaskStatus.COMPLETED.value)

    def test_execute_raises_error_when_pausing_canceled_task(self):
        """Test execute raises TaskAlreadyFinishedError when pausing CANCELED task"""
        task = Task(name="Test Task", priority=1, status=TaskStatus.CANCELED)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime(2024, 1, 1, 10, 0, 0)
        task.actual_end = datetime(2024, 1, 1, 11, 0, 0)
        self.repository.save(task)

        input_dto = PauseTaskRequest(task_id=task.id)

        with self.assertRaises(TaskAlreadyFinishedError) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, task.id)
        self.assertEqual(context.exception.status, TaskStatus.CANCELED.value)


if __name__ == "__main__":
    unittest.main()
