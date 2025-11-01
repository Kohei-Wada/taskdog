"""Tests for TaskController."""

import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock

from domain.entities.task import Task, TaskStatus
from domain.repositories.notes_repository import NotesRepository
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

    def test_add_dependency_adds_to_list(self):
        """Test add_dependency adds dependency to task."""
        # Create two tasks
        dependency = Task(name="Dependency Task", priority=1, status=TaskStatus.PENDING)
        dependency.id = self.repository.generate_next_id()
        self.repository.save(dependency)

        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Add the dependency
        result = self.controller.add_dependency(task.id, dependency.id)

        # Verify dependency added
        self.assertEqual(result.depends_on, [dependency.id])
        self.assertEqual(result.id, task.id)

    def test_add_dependency_persists_changes(self):
        """Test add_dependency persists changes to repository."""
        # Create two tasks
        dependency = Task(name="Dependency Task", priority=1, status=TaskStatus.PENDING)
        dependency.id = self.repository.generate_next_id()
        self.repository.save(dependency)

        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Add the dependency
        self.controller.add_dependency(task.id, dependency.id)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.depends_on, [dependency.id])

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

    def test_set_task_tags_replaces_tags(self):
        """Test set_task_tags replaces existing tags."""
        # Create a task with initial tags
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        task.tags = ["old", "tags"]
        self.repository.save(task)

        # Set new tags
        new_tags = ["new", "tags", "here"]
        result = self.controller.set_task_tags(task.id, new_tags)

        # Verify tags replaced
        self.assertEqual(result.tags, new_tags)
        self.assertEqual(result.id, task.id)

    def test_set_task_tags_persists_changes(self):
        """Test set_task_tags persists changes to repository."""
        # Create a task with initial tags
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        task.tags = ["old"]
        self.repository.save(task)

        # Set new tags
        new_tags = ["work", "urgent"]
        self.controller.set_task_tags(task.id, new_tags)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.tags, new_tags)

    def test_log_hours_adds_to_daily_hours(self):
        """Test log_hours adds hours to actual_daily_hours dict."""
        from datetime import date

        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Log hours for a specific date
        date_str = "2025-11-01"
        hours = 3.5
        result = self.controller.log_hours(task.id, hours, date_str)

        # Verify hours logged
        expected_date = date(2025, 11, 1)
        self.assertEqual(result.actual_daily_hours[expected_date], hours)
        self.assertEqual(result.id, task.id)

    def test_log_hours_persists_changes(self):
        """Test log_hours persists changes to repository."""
        from datetime import date

        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Log hours
        date_str = "2025-11-02"
        hours = 8.0
        self.controller.log_hours(task.id, hours, date_str)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        expected_date = date(2025, 11, 2)
        self.assertEqual(persisted_task.actual_daily_hours[expected_date], hours)

    def test_update_task_single_field(self):
        """Test update_task updates a single field."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Update priority only
        result, updated_fields = self.controller.update_task(task.id, priority=8)

        # Verify priority changed
        self.assertEqual(result.priority, 8)
        self.assertEqual(result.id, task.id)
        self.assertEqual(result.name, "Test Task")  # Other fields unchanged
        self.assertEqual(updated_fields, ["priority"])

    def test_update_task_multiple_fields(self):
        """Test update_task updates multiple fields at once."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Update multiple fields
        new_deadline = datetime(2025, 12, 31, 18, 0)
        result, _updated_fields = self.controller.update_task(
            task.id, name="Updated Task", priority=7, deadline=new_deadline, estimated_duration=5.0
        )

        # Verify all fields updated
        self.assertEqual(result.name, "Updated Task")
        self.assertEqual(result.priority, 7)
        self.assertEqual(result.deadline, new_deadline)
        self.assertEqual(result.estimated_duration, 5.0)
        self.assertEqual(result.id, task.id)

    def test_update_task_returns_updated_fields(self):
        """Test update_task returns list of updated field names."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Update some fields
        _result, updated_fields = self.controller.update_task(
            task.id, priority=5, is_fixed=True, tags=["work", "urgent"]
        )

        # Verify updated fields list
        self.assertIn("priority", updated_fields)
        self.assertIn("is_fixed", updated_fields)
        self.assertIn("tags", updated_fields)
        self.assertEqual(len(updated_fields), 3)

    def test_update_task_persists_changes(self):
        """Test update_task persists changes to repository."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Update task
        new_name = "Updated Name"
        new_priority = 9
        self.controller.update_task(task.id, name=new_name, priority=new_priority)

        # Verify changes persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.name, new_name)
        self.assertEqual(persisted_task.priority, new_priority)

    def test_get_task_detail_with_notes(self):
        """Test get_task_detail retrieves task with notes."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Mock notes repository with notes content
        mock_notes_repo = MagicMock(spec=NotesRepository)
        mock_notes_repo.has_notes.return_value = True
        mock_notes_repo.read_notes.return_value = "# Test Notes\n\nSome content"

        # Create controller with notes repository
        controller_with_notes = TaskController(
            self.repository, self.time_tracker, self.config, mock_notes_repo
        )

        # Get task detail
        result = controller_with_notes.get_task_detail(task.id)

        # Verify result
        self.assertEqual(result.task.id, task.id)
        self.assertEqual(result.task.name, "Test Task")
        self.assertTrue(result.has_notes)
        self.assertEqual(result.notes_content, "# Test Notes\n\nSome content")
        mock_notes_repo.has_notes.assert_called_once_with(task.id)
        mock_notes_repo.read_notes.assert_called_once_with(task.id)

    def test_get_task_detail_without_notes(self):
        """Test get_task_detail retrieves task without notes."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Mock notes repository without notes
        mock_notes_repo = MagicMock(spec=NotesRepository)
        mock_notes_repo.has_notes.return_value = False

        # Create controller with notes repository
        controller_with_notes = TaskController(
            self.repository, self.time_tracker, self.config, mock_notes_repo
        )

        # Get task detail
        result = controller_with_notes.get_task_detail(task.id)

        # Verify result
        self.assertEqual(result.task.id, task.id)
        self.assertEqual(result.task.name, "Test Task")
        self.assertFalse(result.has_notes)
        self.assertIsNone(result.notes_content)
        mock_notes_repo.has_notes.assert_called_once_with(task.id)
        mock_notes_repo.read_notes.assert_not_called()

    def test_get_task_detail_raises_error_when_notes_repository_not_initialized(self):
        """Test get_task_detail raises ValueError when notes_repository is None."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Try to get task detail without notes repository
        with self.assertRaises(ValueError) as context:
            self.controller.get_task_detail(task.id)

        self.assertIn("notes_repository is required", str(context.exception))

    def test_calculate_statistics_returns_result(self):
        """Test calculate_statistics returns StatisticsResult."""
        # Create some tasks with various statuses
        tasks_data = [
            ("Task 1", TaskStatus.PENDING),
            ("Task 2", TaskStatus.COMPLETED),
            ("Task 3", TaskStatus.IN_PROGRESS),
            ("Task 4", TaskStatus.COMPLETED),
            ("Task 5", TaskStatus.CANCELED),
        ]

        for name, status in tasks_data:
            task = Task(name=name, priority=1, status=status)
            task.id = self.repository.generate_next_id()
            self.repository.save(task)

        # Calculate statistics with default period
        result = self.controller.calculate_statistics()

        # Verify result structure
        self.assertIsNotNone(result.task_stats)
        self.assertEqual(result.task_stats.total_tasks, 5)
        self.assertEqual(result.task_stats.completed_count, 2)
        self.assertEqual(result.task_stats.pending_count, 1)
        self.assertEqual(result.task_stats.in_progress_count, 1)
        self.assertEqual(result.task_stats.canceled_count, 1)

    def test_calculate_statistics_with_period_parameter(self):
        """Test calculate_statistics accepts period parameter."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Calculate statistics for different periods
        result_all = self.controller.calculate_statistics(period="all")
        result_7d = self.controller.calculate_statistics(period="7d")
        result_30d = self.controller.calculate_statistics(period="30d")

        # All should return valid results
        self.assertIsNotNone(result_all.task_stats)
        self.assertIsNotNone(result_7d.task_stats)
        self.assertIsNotNone(result_30d.task_stats)

    def test_calculate_statistics_raises_error_for_invalid_period(self):
        """Test calculate_statistics raises ValueError for invalid period."""
        # Try to calculate with invalid period
        with self.assertRaises(ValueError) as context:
            self.controller.calculate_statistics(period="invalid")

        self.assertIn("Invalid period", str(context.exception))


if __name__ == "__main__":
    unittest.main()
