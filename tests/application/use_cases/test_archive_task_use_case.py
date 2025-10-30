"""Tests for ArchiveTaskUseCase."""

import tempfile
import unittest

from application.dto.archive_task_request import ArchiveTaskRequest
from application.use_cases.archive_task import ArchiveTaskUseCase
from domain.entities.task import TaskStatus
from domain.exceptions.task_exceptions import TaskNotFoundException
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class ArchiveTaskUseCaseTest(unittest.TestCase):
    """Test cases for ArchiveTaskUseCase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.temp_file.write("[]")
        self.temp_file.close()

        self.repository = JsonTaskRepository(self.temp_file.name)
        self.use_case = ArchiveTaskUseCase(self.repository)

    def test_archive_completed_task(self):
        """Test archiving a completed task sets is_archived flag and preserves status."""
        # Create completed task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.COMPLETED)

        # Archive task
        input_dto = ArchiveTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived (is_archived=True, status preserved)
        self.assertTrue(result.is_archived)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.daily_allocations, {})

        # Verify persisted
        archived_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(archived_task)
        self.assertTrue(archived_task.is_archived)
        self.assertEqual(archived_task.status, TaskStatus.COMPLETED)

    def test_archive_canceled_task(self):
        """Test archiving a canceled task sets is_archived flag and preserves status."""
        # Create canceled task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.CANCELED)

        # Archive task
        input_dto = ArchiveTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        self.assertTrue(result.is_archived)
        self.assertEqual(result.status, TaskStatus.CANCELED)

    def test_archive_pending_task(self):
        """Test archiving a pending task is allowed and preserves status."""
        # Create pending task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.PENDING)

        # Archive task
        input_dto = ArchiveTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        self.assertTrue(result.is_archived)
        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_archive_in_progress_task(self):
        """Test archiving an in-progress task is allowed and preserves status."""
        # Create in-progress task
        task = self.repository.create(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)

        # Archive task
        input_dto = ArchiveTaskRequest(task_id=task.id)
        result = self.use_case.execute(input_dto)

        # Verify task archived
        self.assertTrue(result.is_archived)
        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)

    def test_archive_nonexistent_task(self):
        """Test archiving a task that doesn't exist."""
        input_dto = ArchiveTaskRequest(task_id=999)

        with self.assertRaises(TaskNotFoundException):
            self.use_case.execute(input_dto)


if __name__ == "__main__":
    unittest.main()
