"""Tests for SqliteTaskRepository."""

import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestSqliteTaskRepository(unittest.TestCase):
    """Test suite for SqliteTaskRepository."""

    def setUp(self) -> None:
        """Set up test fixtures with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_tasks.db"
        self.database_url = f"sqlite:///{self.db_path}"
        self.mapper = TaskDbMapper()
        self.repository = SqliteTaskRepository(self.database_url, self.mapper)

    def tearDown(self) -> None:
        """Clean up database and close connections."""
        self.repository.close()
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_task_generates_id_and_saves(self) -> None:
        """Test create() generates ID and saves task to database."""
        task = self.repository.create("Test Task", priority=1)

        self.assertEqual(task.id, 1)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, 1)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)

        # Verify persistence
        retrieved = self.repository.get_by_id(1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Task")

    def test_save_creates_new_task(self) -> None:
        """Test save() creates a new task in database."""
        task = Task(id=1, name="New Task", priority=1)

        self.repository.save(task)

        retrieved = self.repository.get_by_id(1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "New Task")
        self.assertEqual(retrieved.priority, 1)

    def test_save_updates_existing_task(self) -> None:
        """Test save() updates an existing task."""
        task = Task(id=1, name="Original", priority=1)
        self.repository.save(task)

        # Modify and save again
        task.name = "Updated"
        task.priority = 5
        self.repository.save(task)

        retrieved = self.repository.get_by_id(1)
        self.assertEqual(retrieved.name, "Updated")
        self.assertEqual(retrieved.priority, 5)

    def test_get_all_returns_all_tasks(self) -> None:
        """Test get_all() retrieves all tasks from database."""
        task1 = Task(id=1, name="Task 1", priority=1)
        task2 = Task(id=2, name="Task 2", priority=2)

        self.repository.save(task1)
        self.repository.save(task2)

        all_tasks = self.repository.get_all()

        self.assertEqual(len(all_tasks), 2)
        self.assertEqual(all_tasks[0].name, "Task 1")
        self.assertEqual(all_tasks[1].name, "Task 2")

    def test_get_all_uses_cache(self) -> None:
        """Test get_all() uses in-memory cache."""
        task = Task(id=1, name="Cached Task", priority=1)
        self.repository.save(task)

        # First call loads from database
        first_call = self.repository.get_all()

        # Second call should use cache (same instance)
        second_call = self.repository.get_all()

        self.assertIs(first_call, second_call)

    def test_get_all_cache_invalidated_on_save(self) -> None:
        """Test cache is invalidated when save() is called."""
        task1 = Task(id=1, name="Task 1", priority=1)
        self.repository.save(task1)

        # Load into cache
        first_call = self.repository.get_all()

        # Save another task (should invalidate cache)
        task2 = Task(id=2, name="Task 2", priority=2)
        self.repository.save(task2)

        # Next call should reload from database
        second_call = self.repository.get_all()

        self.assertIsNot(first_call, second_call)
        self.assertEqual(len(second_call), 2)

    def test_get_by_id_returns_task(self) -> None:
        """Test get_by_id() retrieves specific task."""
        task = Task(id=42, name="Specific Task", priority=1)
        self.repository.save(task)

        retrieved = self.repository.get_by_id(42)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, 42)
        self.assertEqual(retrieved.name, "Specific Task")

    def test_get_by_id_returns_none_for_nonexistent(self) -> None:
        """Test get_by_id() returns None for nonexistent task."""
        result = self.repository.get_by_id(999)
        self.assertIsNone(result)

    def test_get_by_ids_returns_multiple_tasks(self) -> None:
        """Test get_by_ids() retrieves multiple tasks in one query."""
        task1 = Task(id=1, name="Task 1", priority=1)
        task2 = Task(id=2, name="Task 2", priority=2)
        task3 = Task(id=3, name="Task 3", priority=3)

        self.repository.save(task1)
        self.repository.save(task2)
        self.repository.save(task3)

        result = self.repository.get_by_ids([1, 3])

        self.assertEqual(len(result), 2)
        self.assertIn(1, result)
        self.assertIn(3, result)
        self.assertEqual(result[1].name, "Task 1")
        self.assertEqual(result[3].name, "Task 3")

    def test_get_by_ids_skips_nonexistent_ids(self) -> None:
        """Test get_by_ids() omits nonexistent task IDs."""
        task1 = Task(id=1, name="Task 1", priority=1)
        self.repository.save(task1)

        result = self.repository.get_by_ids([1, 999])

        self.assertEqual(len(result), 1)
        self.assertIn(1, result)
        self.assertNotIn(999, result)

    def test_get_by_ids_returns_empty_dict_for_empty_list(self) -> None:
        """Test get_by_ids() returns empty dict for empty input."""
        result = self.repository.get_by_ids([])
        self.assertEqual(result, {})

    def test_save_all_saves_multiple_tasks(self) -> None:
        """Test save_all() saves multiple tasks in one transaction."""
        task1 = Task(id=1, name="Task 1", priority=1)
        task2 = Task(id=2, name="Task 2", priority=2)
        task3 = Task(id=3, name="Task 3", priority=3)

        self.repository.save_all([task1, task2, task3])

        all_tasks = self.repository.get_all()
        self.assertEqual(len(all_tasks), 3)

    def test_save_all_with_empty_list(self) -> None:
        """Test save_all() handles empty list gracefully."""
        self.repository.save_all([])
        all_tasks = self.repository.get_all()
        self.assertEqual(len(all_tasks), 0)

    def test_delete_removes_task(self) -> None:
        """Test delete() removes task from database."""
        task = Task(id=1, name="To Delete", priority=1)
        self.repository.save(task)

        self.repository.delete(1)

        retrieved = self.repository.get_by_id(1)
        self.assertIsNone(retrieved)

    def test_delete_nonexistent_task_does_not_error(self) -> None:
        """Test delete() handles nonexistent task gracefully."""
        # Should not raise error
        self.repository.delete(999)

    def test_generate_next_id_starts_at_one(self) -> None:
        """Test generate_next_id() returns 1 for empty database."""
        next_id = self.repository.generate_next_id()
        self.assertEqual(next_id, 1)

    def test_generate_next_id_increments(self) -> None:
        """Test generate_next_id() increments from max ID."""
        task1 = Task(id=1, name="Task 1", priority=1)
        task2 = Task(id=5, name="Task 5", priority=1)

        self.repository.save(task1)
        self.repository.save(task2)

        next_id = self.repository.generate_next_id()
        self.assertEqual(next_id, 6)

    def test_reload_invalidates_cache(self) -> None:
        """Test reload() invalidates in-memory cache."""
        task = Task(id=1, name="Task 1", priority=1)
        self.repository.save(task)

        # Load into cache
        first_call = self.repository.get_all()

        # Reload (should invalidate cache)
        self.repository.reload()

        # Next call should reload from database
        second_call = self.repository.get_all()

        self.assertIsNot(first_call, second_call)

    def test_complex_field_serialization(self) -> None:
        """Test complex fields (daily_allocations, tags, etc.) are persisted correctly."""
        task = Task(
            id=1,
            name="Complex Task",
            priority=1,
            daily_allocations={date(2025, 1, 15): 2.0, date(2025, 1, 16): 3.0},
            actual_daily_hours={date(2025, 1, 15): 1.5},
            depends_on=[2, 3, 5],
            tags=["urgent", "backend"],
        )

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        self.assertEqual(
            retrieved.daily_allocations,
            {date(2025, 1, 15): 2.0, date(2025, 1, 16): 3.0},
        )
        self.assertEqual(retrieved.actual_daily_hours, {date(2025, 1, 15): 1.5})
        self.assertEqual(retrieved.depends_on, [2, 3, 5])
        self.assertEqual(retrieved.tags, ["urgent", "backend"])

    def test_datetime_field_persistence(self) -> None:
        """Test datetime fields are persisted and retrieved correctly."""
        now = datetime(2025, 1, 15, 10, 30, 0)
        deadline = datetime(2025, 1, 20, 18, 0, 0)

        task = Task(
            id=1,
            name="Datetime Test",
            priority=1,
            created_at=now,
            updated_at=now,
            planned_start=datetime(2025, 1, 16, 9, 0, 0),
            planned_end=datetime(2025, 1, 16, 17, 0, 0),
            deadline=deadline,
            actual_start=datetime(2025, 1, 16, 9, 15, 0),
            actual_end=datetime(2025, 1, 16, 16, 45, 0),
        )

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        self.assertEqual(retrieved.created_at, now)
        self.assertEqual(retrieved.deadline, deadline)
        self.assertEqual(retrieved.planned_start, datetime(2025, 1, 16, 9, 0, 0))

    def test_status_enum_persistence(self) -> None:
        """Test TaskStatus enum is persisted correctly."""
        task = Task(id=1, name="Status Test", priority=1, status=TaskStatus.IN_PROGRESS)

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        self.assertEqual(retrieved.status, TaskStatus.IN_PROGRESS)

    def test_boolean_field_persistence(self) -> None:
        """Test boolean fields are persisted correctly."""
        task = Task(
            id=1, name="Boolean Test", priority=1, is_fixed=True, is_archived=True
        )

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        self.assertTrue(retrieved.is_fixed)
        self.assertTrue(retrieved.is_archived)

    def test_optional_fields_with_none(self) -> None:
        """Test optional fields can be None."""
        task = Task(
            id=1,
            name="Minimal Task",
            priority=1,
            planned_start=None,
            planned_end=None,
            deadline=None,
            estimated_duration=None,
        )

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        self.assertIsNone(retrieved.planned_start)
        self.assertIsNone(retrieved.planned_end)
        self.assertIsNone(retrieved.deadline)
        self.assertIsNone(retrieved.estimated_duration)

    def test_persistence_across_repository_instances(self) -> None:
        """Test data persists across different repository instances."""
        task = Task(id=1, name="Persistent Task", priority=1)
        self.repository.save(task)

        # Close first repository
        self.repository.close()

        # Create new repository instance with same database
        new_repository = SqliteTaskRepository(self.database_url, self.mapper)

        retrieved = new_repository.get_by_id(1)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Persistent Task")

        new_repository.close()

    def test_empty_complex_fields_persistence(self) -> None:
        """Test empty complex fields (empty dicts/lists) are persisted correctly."""
        task = Task(
            id=1,
            name="Empty Fields Task",
            priority=1,
            daily_allocations={},
            actual_daily_hours={},
            depends_on=[],
            tags=[],
        )

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        self.assertEqual(retrieved.daily_allocations, {})
        self.assertEqual(retrieved.actual_daily_hours, {})
        self.assertEqual(retrieved.depends_on, [])
        self.assertEqual(retrieved.tags, [])


if __name__ == "__main__":
    unittest.main()
