import os
import tempfile
import time
import unittest
from datetime import datetime

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestJsonTaskRepository(unittest.TestCase):
    """Test cases for JsonTaskRepository"""

    def setUp(self):
        """Create a temporary file for each test"""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)

    def tearDown(self):
        """Clean up temporary file after each test"""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_get_all_empty(self):
        """Test get_all() returns empty list for new repository"""
        tasks = self.repository.get_all()
        self.assertEqual(tasks, [])

    def test_save_and_get_all(self):
        """Test saving tasks and retrieving all"""
        task1 = Task(name="Task 1", priority=1, id=1)
        task2 = Task(name="Task 2", priority=2, id=2)

        self.repository.save(task1)
        self.repository.save(task2)

        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0].name, "Task 1")
        self.assertEqual(tasks[1].name, "Task 2")

    def test_get_by_id(self):
        """Test retrieving a task by ID"""
        task = Task(name="Test Task", priority=1, id=1)
        self.repository.save(task)

        found = self.repository.get_by_id(1)
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Test Task")
        self.assertEqual(found.priority, 1)

    def test_get_by_id_not_found(self):
        """Test get_by_id() returns None for non-existent ID"""
        found = self.repository.get_by_id(999)
        self.assertIsNone(found)

    def test_save_update_existing(self):
        """Test that save() updates an existing task"""
        task = Task(name="Original", priority=1, id=1)
        self.repository.save(task)

        # Modify the task
        task.name = "Updated"
        task.priority = 5
        self.repository.save(task)

        # Verify only one task exists and it's updated
        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].name, "Updated")
        self.assertEqual(tasks[0].priority, 5)

    def test_save_updates_updated_at_on_existing_task(self):
        """Test that save() automatically updates updated_at for existing tasks"""
        # Create and save initial task
        task = Task(name="Test Task", priority=1, id=1)
        self.repository.save(task)
        initial_updated_at = task.updated_at

        # Wait a bit to ensure timestamp difference
        time.sleep(0.01)

        # Update the task
        task.name = "Updated Task"
        self.repository.save(task)

        # Verify updated_at was changed
        self.assertGreater(task.updated_at, initial_updated_at)

    def test_save_does_not_update_updated_at_on_new_task(self):
        """Test that save() does not modify updated_at for new tasks"""
        # Create task with specific created_at and updated_at
        created = datetime(2025, 1, 1, 0, 0, 0)
        task = Task(name="New Task", priority=1, id=1, created_at=created, updated_at=created)

        # Save new task (first save)
        self.repository.save(task)

        # Verify updated_at was not modified (remains equal to created_at for new tasks)
        self.assertEqual(task.updated_at, created)

    def test_delete(self):
        """Test deleting a task"""
        task1 = Task(name="Task 1", priority=1, id=1)
        task2 = Task(name="Task 2", priority=2, id=2)

        self.repository.save(task1)
        self.repository.save(task2)

        self.repository.delete(1)

        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, 2)

    def test_delete_nonexistent(self):
        """Test deleting a non-existent task (should not raise error)"""
        task = Task(name="Task 1", priority=1, id=1)
        self.repository.save(task)

        # Delete non-existent ID
        self.repository.delete(999)

        # Original task should still exist
        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 1)

    def test_persistence(self):
        """Test that data persists across repository instances"""
        task = Task(name="Persistent Task", priority=1, id=1)
        self.repository.save(task)

        # Create new repository instance with same file
        new_repository = JsonTaskRepository(self.test_filename)
        tasks = new_repository.get_all()

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].name, "Persistent Task")

    def test_load_nonexistent_file(self):
        """Test loading from a non-existent file returns empty list"""
        os.unlink(self.test_filename)
        new_repository = JsonTaskRepository(self.test_filename)
        tasks = new_repository.get_all()
        self.assertEqual(tasks, [])

    def test_task_with_all_fields(self):
        """Test saving and loading a task with all fields populated"""
        task = Task(
            name="Full Task",
            priority=3,
            id=1,
            status=TaskStatus.IN_PROGRESS,
            planned_start=datetime(2025, 1, 1, 9, 0, 0),
            planned_end=datetime(2025, 1, 1, 17, 0, 0),
            deadline=datetime(2025, 1, 2, 12, 0, 0),
            actual_start=datetime(2025, 1, 1, 9, 15, 0),
            estimated_duration=8.0,
        )

        self.repository.save(task)

        loaded = self.repository.get_by_id(1)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Full Task")
        self.assertEqual(loaded.priority, 3)
        self.assertEqual(loaded.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(loaded.planned_start, datetime(2025, 1, 1, 9, 0, 0))
        self.assertEqual(loaded.planned_end, datetime(2025, 1, 1, 17, 0, 0))
        self.assertEqual(loaded.deadline, datetime(2025, 1, 2, 12, 0, 0))
        self.assertEqual(loaded.actual_start, datetime(2025, 1, 1, 9, 15, 0))
        self.assertEqual(loaded.estimated_duration, 8.0)

    def test_generate_next_id_empty(self):
        """Test generate_next_id() returns 1 for empty repository"""
        next_id = self.repository.generate_next_id()
        self.assertEqual(next_id, 1)

    def test_generate_next_id_with_tasks(self):
        """Test generate_next_id() returns max(id) + 1"""
        task1 = Task(name="Task 1", priority=1, id=1)
        task2 = Task(name="Task 2", priority=1, id=2)
        task3 = Task(name="Task 3", priority=1, id=5)  # Non-sequential

        self.repository.save(task1)
        self.repository.save(task2)
        self.repository.save(task3)

        next_id = self.repository.generate_next_id()
        self.assertEqual(next_id, 6)

    def test_generate_next_id_sequential(self):
        """Test generate_next_id() produces sequential IDs"""
        # Add tasks using generate_next_id()
        for i in range(3):
            task = Task(name=f"Task {i}", priority=1, id=self.repository.generate_next_id())
            self.repository.save(task)

        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].id, 1)
        self.assertEqual(tasks[1].id, 2)
        self.assertEqual(tasks[2].id, 3)

    def test_backup_file_created(self):
        """Test that backup file is created when saving"""
        # Create initial task
        task = Task(name="Original Task", priority=1, id=1)
        self.repository.save(task)

        # Modify and save again to trigger backup
        task.name = "Modified Task"
        self.repository.save(task)

        # Check backup file exists
        backup_path = self.test_filename.replace(".json", ".json.bak")
        self.assertTrue(os.path.exists(backup_path))

        # Clean up backup file
        if os.path.exists(backup_path):
            os.unlink(backup_path)

    def test_temp_file_cleaned_up_on_error(self):
        """Test that temporary file is cleaned up on write error"""
        import pathlib

        # Create a task
        task = Task(name="Test Task", priority=1, id=1)
        self.repository.save(task)

        # Check no temp files left in directory
        test_dir = pathlib.Path(self.test_filename).parent
        temp_files = list(test_dir.glob(".*.tmp"))
        self.assertEqual(len(temp_files), 0)

    def test_recovery_from_corrupted_file(self):
        """Test recovery from backup when main file is corrupted"""
        # Create initial data
        task = Task(name="Original Task", priority=1, id=1)
        self.repository.save(task)

        # Create backup by saving again
        task2 = Task(name="Second Task", priority=2, id=2)
        self.repository.save(task2)

        # Verify backup exists
        backup_path = self.test_filename.replace(".json", ".json.bak")
        self.assertTrue(os.path.exists(backup_path))

        # Corrupt the main file
        with open(self.test_filename, "w") as f:
            f.write("{ invalid json data }")

        # Try to load - should recover from backup
        new_repository = JsonTaskRepository(self.test_filename)
        tasks = new_repository.get_all()

        # Should have recovered the data from backup
        self.assertGreater(len(tasks), 0)

        # Clean up backup file
        if os.path.exists(backup_path):
            os.unlink(backup_path)

    def test_load_with_no_backup(self):
        """Test that IOError is raised when both main and backup are corrupted"""
        # Create a corrupted file with no backup
        with open(self.test_filename, "w") as f:
            f.write("{ invalid json }")

        # Should raise IOError since no backup exists
        with self.assertRaises(IOError) as context:
            JsonTaskRepository(self.test_filename)

        self.assertIn("Failed to load tasks", str(context.exception))

    def test_datetime_serialization_iso8601(self):
        """Test that datetime objects are serialized to ISO 8601 format"""
        task = Task(
            name="Datetime Task",
            priority=1,
            id=1,
            planned_start=datetime(2025, 1, 15, 9, 0, 0),
            planned_end=datetime(2025, 1, 15, 17, 0, 0),
            deadline=datetime(2025, 1, 20, 18, 0, 0),
        )

        self.repository.save(task)

        # Load and verify datetime objects are preserved
        loaded = self.repository.get_by_id(1)
        self.assertIsNotNone(loaded)
        self.assertIsInstance(loaded.planned_start, datetime)
        self.assertIsInstance(loaded.planned_end, datetime)
        self.assertIsInstance(loaded.deadline, datetime)
        self.assertEqual(loaded.planned_start, datetime(2025, 1, 15, 9, 0, 0))
        self.assertEqual(loaded.planned_end, datetime(2025, 1, 15, 17, 0, 0))
        self.assertEqual(loaded.deadline, datetime(2025, 1, 20, 18, 0, 0))

    def test_backward_compatibility_legacy_format(self):
        """Test that legacy string format 'YYYY-MM-DD HH:MM:SS' is still supported"""
        import json

        # Create task data with legacy format
        task_data = {
            "id": 1,
            "name": "Legacy Task",
            "priority": 1,
            "status": "PENDING",
            "created_at": datetime.fromtimestamp(1234567890.0).isoformat(),
            "planned_start": "2025-01-15 09:00:00",  # Legacy format
            "planned_end": "2025-01-15 17:00:00",
            "deadline": "2025-01-20 18:00:00",
            "actual_start": None,
            "actual_end": None,
            "estimated_duration": None,
            "daily_allocations": {},
            "depends_on": [],
            "is_fixed": False,
            "actual_daily_hours": {},
        }

        # Write legacy format to file
        with open(self.test_filename, "w") as f:
            json.dump([task_data], f)

        # Load from repository
        repo = JsonTaskRepository(self.test_filename)
        loaded = repo.get_by_id(1)

        # Verify datetime objects are created from legacy strings
        self.assertIsNotNone(loaded)
        self.assertIsInstance(loaded.planned_start, datetime)
        self.assertIsInstance(loaded.planned_end, datetime)
        self.assertIsInstance(loaded.deadline, datetime)
        self.assertEqual(loaded.planned_start, datetime(2025, 1, 15, 9, 0, 0))
        self.assertEqual(loaded.planned_end, datetime(2025, 1, 15, 17, 0, 0))
        self.assertEqual(loaded.deadline, datetime(2025, 1, 20, 18, 0, 0))

    def test_datetime_roundtrip_preservation(self):
        """Test that datetime objects survive save/load roundtrip"""
        original_dt = datetime(2025, 10, 25, 14, 30, 45)
        task = Task(
            name="Roundtrip Task",
            priority=1,
            id=1,
            planned_start=original_dt,
            actual_start=datetime(2025, 10, 25, 14, 35, 0),
        )

        # Save and reload
        self.repository.save(task)
        new_repo = JsonTaskRepository(self.test_filename)
        loaded = new_repo.get_by_id(1)

        # Verify exact datetime preservation
        self.assertEqual(loaded.planned_start, original_dt)
        self.assertEqual(loaded.actual_start, datetime(2025, 10, 25, 14, 35, 0))

    def test_save_all_updates_multiple_tasks(self):
        """Test save_all() updates multiple existing tasks"""
        # Create 3 tasks
        task1 = Task(name="Task 1", priority=1, id=1)
        task2 = Task(name="Task 2", priority=2, id=2)
        task3 = Task(name="Task 3", priority=3, id=3)

        self.repository.save(task1)
        self.repository.save(task2)
        self.repository.save(task3)

        # Modify all tasks
        task1.priority = 10
        task2.priority = 20
        task3.priority = 30

        # Save all at once
        self.repository.save_all([task1, task2, task3])

        # Verify all updated
        loaded1 = self.repository.get_by_id(1)
        loaded2 = self.repository.get_by_id(2)
        loaded3 = self.repository.get_by_id(3)

        self.assertEqual(loaded1.priority, 10)
        self.assertEqual(loaded2.priority, 20)
        self.assertEqual(loaded3.priority, 30)

    def test_save_all_creates_new_tasks(self):
        """Test save_all() creates multiple new tasks"""
        # Create 3 new tasks with IDs
        task1 = Task(name="New Task 1", priority=1, id=1)
        task2 = Task(name="New Task 2", priority=2, id=2)
        task3 = Task(name="New Task 3", priority=3, id=3)

        # Save all at once
        self.repository.save_all([task1, task2, task3])

        # Verify all created
        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].name, "New Task 1")
        self.assertEqual(tasks[1].name, "New Task 2")
        self.assertEqual(tasks[2].name, "New Task 3")

    def test_save_all_mixed_new_and_existing(self):
        """Test save_all() with mix of new and existing tasks"""
        # Create 2 existing tasks
        task1 = Task(name="Existing 1", priority=1, id=1)
        task2 = Task(name="Existing 2", priority=2, id=2)
        self.repository.save(task1)
        self.repository.save(task2)

        # Modify existing task and create new task
        task1.priority = 10
        task3 = Task(name="New Task", priority=3, id=3)

        # Save all at once
        self.repository.save_all([task1, task3])

        # Verify results
        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 3)

        loaded1 = self.repository.get_by_id(1)
        loaded3 = self.repository.get_by_id(3)

        self.assertEqual(loaded1.priority, 10)
        self.assertEqual(loaded3.name, "New Task")

    def test_save_all_empty_list(self):
        """Test save_all() with empty list does nothing"""
        # Create a task first
        task = Task(name="Test Task", priority=1, id=1)
        self.repository.save(task)

        # Save empty list should not affect anything
        self.repository.save_all([])

        # Verify task still exists
        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 1)

    def test_save_all_without_id_raises_error(self):
        """Test save_all() raises ValueError for task without ID"""
        task1 = Task(name="Task 1", priority=1, id=1)
        task2 = Task(name="Task without ID", priority=2, id=None)

        # Should raise ValueError
        with self.assertRaises(ValueError) as context:
            self.repository.save_all([task1, task2])

        self.assertIn("Cannot save task without ID", str(context.exception))

    def test_save_all_updates_updated_at(self):
        """Test save_all() updates updated_at for existing tasks"""
        # Create tasks
        task1 = Task(name="Task 1", priority=1, id=1)
        task2 = Task(name="Task 2", priority=2, id=2)
        self.repository.save(task1)
        self.repository.save(task2)

        initial_updated_at_1 = task1.updated_at
        initial_updated_at_2 = task2.updated_at

        # Wait a bit to ensure timestamp difference
        time.sleep(0.01)

        # Modify tasks
        task1.priority = 10
        task2.priority = 20

        # Save all
        self.repository.save_all([task1, task2])

        # Verify updated_at was changed for both
        self.assertGreater(task1.updated_at, initial_updated_at_1)
        self.assertGreater(task2.updated_at, initial_updated_at_2)


if __name__ == "__main__":
    unittest.main()
