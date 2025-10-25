"""Tests for ArchiveTaskUseCase."""

import tempfile
import unittest

from application.dto.archive_task_request import ArchiveTaskRequest
from application.use_cases.archive_task import ArchiveTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class ArchiveTaskUseCaseTest(unittest.TestCase):
    """Test cases for ArchiveTaskUseCase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.temp_file.write("[]")
        self.temp_file.close()

        self.repository = JsonTaskRepository(self.temp_file.name)
        self.time_tracker = TimeTracker()
        self.use_case = ArchiveTaskUseCase(self.repository, self.time_tracker)

    def test_archive_completed_task(self):
        """Test archiving a completed task changes status to ARCHIVED."""
        # Create completed task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.COMPLETED)

        # Archive task
        input_dto = ArchiveTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived (status = ARCHIVED)
        self.assertEqual(result.status, TaskStatus.ARCHIVED)
        self.assertEqual(result.daily_allocations, {})

        # Verify persisted
        archived_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(archived_task)
        self.assertEqual(archived_task.status, TaskStatus.ARCHIVED)

    def test_archive_canceled_task(self):
        """Test archiving a canceled task changes status to ARCHIVED."""
        # Create canceled task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.CANCELED)

        # Archive task
        input_dto = ArchiveTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        self.assertEqual(result.status, TaskStatus.ARCHIVED)

    def test_archive_pending_task(self):
        """Test archiving a pending task is allowed."""
        # Create pending task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.PENDING)

        # Archive task
        input_dto = ArchiveTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        self.assertEqual(result.status, TaskStatus.ARCHIVED)

    def test_archive_in_progress_task(self):
        """Test archiving an in-progress task is allowed."""
        # Create in-progress task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)

        # Archive task
        input_dto = ArchiveTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        self.assertEqual(result.status, TaskStatus.ARCHIVED)

    def test_archive_nonexistent_task(self):
        """Test archiving a task that doesn't exist."""
        input_dto = ArchiveTaskRequest(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)


if __name__ == "__main__":
    unittest.main()
