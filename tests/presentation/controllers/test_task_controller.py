"""Tests for TaskController."""

import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock

from domain.entities.task import Task, TaskStatus
from domain.services.time_tracker import TimeTracker
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from presentation.controllers.task_controller import TaskController


class TestTaskController(unittest.TestCase):
    """Test cases for TaskController."""

    def setUp(self):
        """Create temporary file and initialize controller for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.time_tracker = TimeTracker()
        # Mock config with task.default_priority
        self.config = MagicMock()
        self.config.task = MagicMock()
        self.config.task.default_priority = 5  # Default for most tests
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

    def test_pause_task_changes_status_to_pending(self):
        """Test pause_task changes task status to PENDING."""
        # Create and start a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Pause the task
        result = self.controller.pause_task(task.id)

        # Verify status changed
        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertEqual(result.id, task.id)

    def test_pause_task_clears_timestamps(self):
        """Test pause_task clears actual start/end timestamps."""
        # Create and start a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Pause the task
        result = self.controller.pause_task(task.id)

        # Verify timestamps are cleared
        self.assertIsNone(result.actual_start)
        self.assertIsNone(result.actual_end)

    def test_cancel_task_changes_status_to_canceled(self):
        """Test cancel_task changes task status to CANCELED."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Cancel the task
        result = self.controller.cancel_task(task.id)

        # Verify status changed
        self.assertEqual(result.status, TaskStatus.CANCELED)
        self.assertEqual(result.id, task.id)

    def test_cancel_task_records_actual_end_time(self):
        """Test cancel_task records actual_end timestamp."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.IN_PROGRESS)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Cancel the task
        result = self.controller.cancel_task(task.id)

        # Verify actual_end is set
        self.assertIsNotNone(result.actual_end)

    def test_create_task_basic(self):
        """Test create_task creates a task with basic fields."""
        # Create task
        result = self.controller.create_task("New Task", priority=3)

        # Verify task created
        self.assertIsNotNone(result.id)
        self.assertEqual(result.name, "New Task")
        self.assertEqual(result.priority, 3)
        self.assertEqual(result.status, TaskStatus.PENDING)

    def test_create_task_with_all_fields(self):
        """Test create_task with all optional fields."""
        deadline = datetime(2025, 12, 31, 18, 0)
        planned_start = datetime(2025, 11, 1, 9, 0)
        planned_end = datetime(2025, 11, 1, 17, 0)

        # Create task
        result = self.controller.create_task(
            name="Complex Task",
            priority=8,
            deadline=deadline,
            estimated_duration=16.5,
            planned_start=planned_start,
            planned_end=planned_end,
            is_fixed=True,
            tags=["work", "urgent"],
        )

        # Verify all fields
        self.assertIsNotNone(result.id)
        self.assertEqual(result.name, "Complex Task")
        self.assertEqual(result.priority, 8)
        self.assertEqual(result.deadline, deadline)
        self.assertEqual(result.estimated_duration, 16.5)
        self.assertEqual(result.planned_start, planned_start)
        self.assertEqual(result.planned_end, planned_end)
        self.assertTrue(result.is_fixed)
        self.assertEqual(result.tags, ["work", "urgent"])

    def test_create_task_uses_default_priority(self):
        """Test create_task uses config default priority when not specified."""
        # Mock config
        self.config.task.default_priority = 7

        # Create task without priority
        result = self.controller.create_task("Task with Default Priority")

        # Verify default priority used
        self.assertEqual(result.priority, 7)

    def test_reopen_task_changes_status_to_pending(self):
        """Test reopen_task changes task status to PENDING."""
        # Create a completed task
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Reopen the task
        result = self.controller.reopen_task(task.id)

        # Verify status changed
        self.assertEqual(result.status, TaskStatus.PENDING)
        self.assertEqual(result.id, task.id)

    def test_reopen_task_clears_timestamps(self):
        """Test reopen_task clears actual start/end timestamps."""
        # Create a completed task with timestamps
        task = Task(name="Test Task", priority=1, status=TaskStatus.COMPLETED)
        task.id = self.repository.generate_next_id()
        task.actual_start = datetime.now()
        task.actual_end = datetime.now()
        self.repository.save(task)

        # Reopen the task
        result = self.controller.reopen_task(task.id)

        # Verify timestamps are cleared
        self.assertIsNone(result.actual_start)
        self.assertIsNone(result.actual_end)

    def test_archive_task_sets_archived_flag(self):
        """Test archive_task sets is_archived to True."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Archive the task
        result = self.controller.archive_task(task.id)

        # Verify is_archived is True
        self.assertTrue(result.is_archived)
        self.assertEqual(result.id, task.id)

    def test_archive_task_persists_changes(self):
        """Test archive_task persists changes to repository."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Archive the task
        self.controller.archive_task(task.id)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertTrue(persisted_task.is_archived)

    def test_remove_task_deletes_task(self):
        """Test remove_task permanently deletes the task."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Remove the task
        self.controller.remove_task(task.id)

        # Verify task is deleted
        deleted_task = self.repository.get_by_id(task.id)
        self.assertIsNone(deleted_task)

    def test_restore_task_clears_archived_flag(self):
        """Test restore_task sets is_archived to False."""
        # Create an archived task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        task.is_archived = True
        self.repository.save(task)

        # Restore the task
        result = self.controller.restore_task(task.id)

        # Verify is_archived is False
        self.assertFalse(result.is_archived)
        self.assertEqual(result.id, task.id)

    def test_restore_task_persists_changes(self):
        """Test restore_task persists changes to repository."""
        # Create an archived task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        task.is_archived = True
        self.repository.save(task)

        # Restore the task
        self.controller.restore_task(task.id)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertFalse(persisted_task.is_archived)

    def test_remove_dependency_removes_from_list(self):
        """Test remove_dependency removes dependency from task."""
        # Create two tasks with dependency
        dependency = Task(name="Dependency Task", priority=1, status=TaskStatus.PENDING)
        dependency.id = self.repository.generate_next_id()
        self.repository.save(dependency)

        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        task.depends_on = [dependency.id]
        self.repository.save(task)

        # Remove the dependency
        result = self.controller.remove_dependency(task.id, dependency.id)

        # Verify dependency removed
        self.assertEqual(result.depends_on, [])
        self.assertEqual(result.id, task.id)

    def test_remove_dependency_persists_changes(self):
        """Test remove_dependency persists changes to repository."""
        # Create two tasks with dependency
        dependency = Task(name="Dependency Task", priority=1, status=TaskStatus.PENDING)
        dependency.id = self.repository.generate_next_id()
        self.repository.save(dependency)

        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        task.depends_on = [dependency.id]
        self.repository.save(task)

        # Remove the dependency
        self.controller.remove_dependency(task.id, dependency.id)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.depends_on, [])


if __name__ == "__main__":
    unittest.main()
