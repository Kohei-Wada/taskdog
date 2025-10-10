import unittest
import os
import tempfile
import json
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from domain.entities.task import Task, TaskStatus


class TestJsonTaskRepository(unittest.TestCase):
    """Test cases for JsonTaskRepository"""

    def setUp(self):
        """Create a temporary file for each test"""
        self.test_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        )
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

    def test_get_children(self):
        """Test retrieving child tasks"""
        parent = Task(name="Parent", priority=1, id=1)
        child1 = Task(name="Child 1", priority=1, id=2, parent_id=1)
        child2 = Task(name="Child 2", priority=1, id=3, parent_id=1)
        other = Task(name="Other", priority=1, id=4)

        self.repository.save(parent)
        self.repository.save(child1)
        self.repository.save(child2)
        self.repository.save(other)

        children = self.repository.get_children(1)
        self.assertEqual(len(children), 2)
        child_names = [c.name for c in children]
        self.assertIn("Child 1", child_names)
        self.assertIn("Child 2", child_names)

    def test_get_children_empty(self):
        """Test get_children() returns empty list when no children"""
        parent = Task(name="Parent", priority=1, id=1)
        self.repository.save(parent)

        children = self.repository.get_children(1)
        self.assertEqual(children, [])

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
            parent_id=None,
            planned_start="2025-01-01 09:00:00",
            planned_end="2025-01-01 17:00:00",
            deadline="2025-01-02 12:00:00",
            actual_start="2025-01-01 09:15:00",
            estimated_duration=8.0,
        )

        self.repository.save(task)

        loaded = self.repository.get_by_id(1)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Full Task")
        self.assertEqual(loaded.priority, 3)
        self.assertEqual(loaded.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(loaded.planned_start, "2025-01-01 09:00:00")
        self.assertEqual(loaded.planned_end, "2025-01-01 17:00:00")
        self.assertEqual(loaded.deadline, "2025-01-02 12:00:00")
        self.assertEqual(loaded.actual_start, "2025-01-01 09:15:00")
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
            task = Task(
                name=f"Task {i}", priority=1, id=self.repository.generate_next_id()
            )
            self.repository.save(task)

        tasks = self.repository.get_all()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].id, 1)
        self.assertEqual(tasks[1].id, 2)
        self.assertEqual(tasks[2].id, 3)


if __name__ == "__main__":
    unittest.main()
