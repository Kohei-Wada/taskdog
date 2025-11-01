"""Tests for TaskController."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock

from domain.entities.task import Task, TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.controllers.task_controller import TaskController
from shared.config_manager import ConfigManager


class TestTaskController(unittest.TestCase):
    """Test cases for TaskController."""

    def setUp(self):
        """Create temporary file and initialize controller for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        self.config = MagicMock(spec=ConfigManager)
        self.controller = TaskController(self.repository, self.time_tracker, self.config)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_start_task_changes_status_to_in_progress(self):
        """Test start_task changes task status to IN_PROGRESS."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Start the task
        result = self.controller.start_task(task.id)

        # Verify status changed
        self.assertEqual(result.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(result.id, task.id)
        self.assertEqual(result.name, "Test Task")

    def test_start_task_records_actual_start_time(self):
        """Test start_task records actual_start timestamp."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Start the task
        result = self.controller.start_task(task.id)

        # Verify actual_start is set
        self.assertIsNotNone(result.actual_start)
        self.assertIsNone(result.actual_end)

    def test_start_task_persists_changes(self):
        """Test start_task persists changes to repository."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Start the task
        self.controller.start_task(task.id)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(persisted_task.actual_start)

    def test_complete_task_changes_status_to_completed(self):
        """Test complete_task changes task status to COMPLETED."""
        # Create and start a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Complete the task
        result = self.controller.complete_task(task.id)

        # Verify status changed
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        self.assertEqual(result.id, task.id)
        self.assertEqual(result.name, "Test Task")

    def test_complete_task_records_actual_end_time(self):
        """Test complete_task records actual_end timestamp."""
        # Create and start a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Complete the task
        result = self.controller.complete_task(task.id)

        # Verify actual_end is set
        self.assertIsNotNone(result.actual_end)

    def test_complete_task_persists_changes(self):
        """Test complete_task persists changes to repository."""
        # Create and start a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Complete the task
        self.controller.complete_task(task.id)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(persisted_task.actual_end)


if __name__ == "__main__":
    unittest.main()
