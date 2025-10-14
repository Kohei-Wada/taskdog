"""Tests for ArchiveTaskUseCase."""

import tempfile
import unittest

from application.dto.archive_task_input import ArchiveTaskInput
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

    def test_archive_task(self):
        """Test archiving a task."""
        # Create task
        task = self.repository.create(name="Test Task", priority=1)

        # Archive task
        input_dto = ArchiveTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify task archived
        archived_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(archived_task)
        self.assertEqual(archived_task.status, TaskStatus.ARCHIVED)
        self.assertEqual(archived_task.daily_allocations, {})

    def test_archive_task_with_allocations(self):
        """Test archiving a task clears daily allocations."""
        # Create task with schedule
        task = self.repository.create(name="Test Task", priority=1)
        task.daily_allocations = {"2025-10-16": 4.0, "2025-10-17": 3.0}
        self.repository.save(task)

        # Archive task
        input_dto = ArchiveTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify allocations cleared
        archived_task = self.repository.get_by_id(task.id)
        self.assertEqual(archived_task.status, TaskStatus.ARCHIVED)
        self.assertEqual(archived_task.daily_allocations, {})

    def test_archive_nonexistent_task(self):
        """Test archiving a task that doesn't exist."""
        input_dto = ArchiveTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_archive_completed_task(self):
        """Test archiving an already completed task."""
        # Create completed task
        task = self.repository.create(name="Test Task", priority=1)
        task.status = TaskStatus.COMPLETED
        self.repository.save(task)

        # Archive task
        input_dto = ArchiveTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify task archived
        archived_task = self.repository.get_by_id(task.id)
        self.assertEqual(archived_task.status, TaskStatus.ARCHIVED)

    def test_archive_in_progress_task(self):
        """Test archiving an in-progress task."""
        # Create in-progress task
        task = self.repository.create(name="Test Task", priority=1)
        task.status = TaskStatus.IN_PROGRESS
        self.repository.save(task)

        # Archive task
        input_dto = ArchiveTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify task archived
        archived_task = self.repository.get_by_id(task.id)
        self.assertEqual(archived_task.status, TaskStatus.ARCHIVED)


if __name__ == "__main__":
    unittest.main()
