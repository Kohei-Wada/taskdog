"""Tests for JSON to SQLite data migration."""

import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from domain.entities.task import Task, TaskStatus
from infrastructure.persistence.database.sqlite_task_repository import SqliteTaskRepository
from infrastructure.persistence.json_task_repository import JsonTaskRepository
from infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper
from infrastructure.persistence.mappers.task_json_mapper import TaskJsonMapper


class TestJsonToSqliteMigration(unittest.TestCase):
    """Test suite for migrating data from JSON to SQLite."""

    def setUp(self) -> None:
        """Set up test fixtures with temporary files."""
        self.temp_dir = tempfile.mkdtemp()
        self.json_file = str(Path(self.temp_dir) / "tasks.json")
        self.db_file = str(Path(self.temp_dir) / "tasks.db")
        self.database_url = f"sqlite:///{self.db_file}"

        self.json_mapper = TaskJsonMapper()
        self.db_mapper = TaskDbMapper()

    def tearDown(self) -> None:
        """Clean up test files."""
        import shutil

        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_simple_task_migration(self) -> None:
        """Test migrating a simple task from JSON to SQLite."""
        # Create task in JSON repository
        json_repo = JsonTaskRepository(self.json_file, self.json_mapper)
        original_task = json_repo.create("Test Task", priority=1)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository(self.database_url, self.db_mapper)
        all_tasks = json_repo.get_all()
        sqlite_repo.save_all(all_tasks)

        # Verify migration
        migrated_task = sqlite_repo.get_by_id(original_task.id)
        self.assertIsNotNone(migrated_task)
        self.assertEqual(migrated_task.name, original_task.name)
        self.assertEqual(migrated_task.priority, original_task.priority)

        sqlite_repo.close()

    def test_complex_task_migration(self) -> None:
        """Test migrating a task with complex fields from JSON to SQLite."""
        # Create complex task in JSON repository
        json_repo = JsonTaskRepository(self.json_file, self.json_mapper)

        complex_task = Task(
            id=1,
            name="Complex Migration Task",
            priority=5,
            status=TaskStatus.IN_PROGRESS,
            created_at=datetime(2025, 1, 1, 0, 0, 0),
            updated_at=datetime(2025, 1, 2, 0, 0, 0),
            planned_start=datetime(2025, 1, 15, 9, 0, 0),
            planned_end=datetime(2025, 1, 15, 17, 0, 0),
            deadline=datetime(2025, 1, 20, 18, 0, 0),
            actual_start=datetime(2025, 1, 15, 9, 15, 0),
            estimated_duration=8.0,
            is_fixed=True,
            daily_allocations={date(2025, 1, 15): 4.0, date(2025, 1, 16): 4.0},
            actual_daily_hours={date(2025, 1, 15): 3.5},
            depends_on=[2, 3],
            tags=["urgent", "backend", "database"],
            is_archived=False,
        )

        json_repo.save(complex_task)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository(self.database_url, self.db_mapper)
        all_tasks = json_repo.get_all()
        sqlite_repo.save_all(all_tasks)

        # Verify all fields migrated correctly
        migrated = sqlite_repo.get_by_id(1)

        self.assertEqual(migrated.name, "Complex Migration Task")
        self.assertEqual(migrated.priority, 5)
        self.assertEqual(migrated.status, TaskStatus.IN_PROGRESS)
        self.assertEqual(migrated.created_at, datetime(2025, 1, 1, 0, 0, 0))
        self.assertEqual(migrated.updated_at, datetime(2025, 1, 2, 0, 0, 0))
        self.assertEqual(migrated.planned_start, datetime(2025, 1, 15, 9, 0, 0))
        self.assertEqual(migrated.planned_end, datetime(2025, 1, 15, 17, 0, 0))
        self.assertEqual(migrated.deadline, datetime(2025, 1, 20, 18, 0, 0))
        self.assertEqual(migrated.actual_start, datetime(2025, 1, 15, 9, 15, 0))
        self.assertEqual(migrated.estimated_duration, 8.0)
        self.assertTrue(migrated.is_fixed)
        self.assertEqual(
            migrated.daily_allocations, {date(2025, 1, 15): 4.0, date(2025, 1, 16): 4.0}
        )
        self.assertEqual(migrated.actual_daily_hours, {date(2025, 1, 15): 3.5})
        self.assertEqual(migrated.depends_on, [2, 3])
        self.assertEqual(migrated.tags, ["urgent", "backend", "database"])
        self.assertFalse(migrated.is_archived)

        sqlite_repo.close()

    def test_multiple_tasks_migration(self) -> None:
        """Test migrating multiple tasks from JSON to SQLite."""
        # Create multiple tasks in JSON repository
        json_repo = JsonTaskRepository(self.json_file, self.json_mapper)

        task1 = json_repo.create("Task 1", priority=1, tags=["tag1"])
        task2 = json_repo.create("Task 2", priority=2, is_fixed=True)
        task3 = json_repo.create("Task 3", priority=3, status=TaskStatus.COMPLETED)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository(self.database_url, self.db_mapper)
        all_tasks = json_repo.get_all()
        sqlite_repo.save_all(all_tasks)

        # Verify all tasks migrated
        all_migrated = sqlite_repo.get_all()
        self.assertEqual(len(all_migrated), 3)

        # Verify individual tasks
        migrated1 = sqlite_repo.get_by_id(task1.id)
        migrated2 = sqlite_repo.get_by_id(task2.id)
        migrated3 = sqlite_repo.get_by_id(task3.id)

        self.assertEqual(migrated1.name, "Task 1")
        self.assertEqual(migrated1.tags, ["tag1"])
        self.assertEqual(migrated2.name, "Task 2")
        self.assertTrue(migrated2.is_fixed)
        self.assertEqual(migrated3.name, "Task 3")
        self.assertEqual(migrated3.status, TaskStatus.COMPLETED)

        sqlite_repo.close()

    def test_empty_repository_migration(self) -> None:
        """Test migrating an empty JSON repository to SQLite."""
        # Create empty JSON repository
        json_repo = JsonTaskRepository(self.json_file, self.json_mapper)

        # Migrate to SQLite
        sqlite_repo = SqliteTaskRepository(self.database_url, self.db_mapper)
        all_tasks = json_repo.get_all()
        sqlite_repo.save_all(all_tasks)

        # Verify SQLite repository is also empty
        all_migrated = sqlite_repo.get_all()
        self.assertEqual(len(all_migrated), 0)

        sqlite_repo.close()

    def test_backward_migration_sqlite_to_json(self) -> None:
        """Test migrating data back from SQLite to JSON (rollback scenario)."""
        # Create tasks in SQLite repository
        sqlite_repo = SqliteTaskRepository(self.database_url, self.db_mapper)

        task1 = sqlite_repo.create("SQLite Task 1", priority=1)
        task2 = sqlite_repo.create("SQLite Task 2", priority=2, tags=["rollback"])

        # Migrate back to JSON
        json_repo = JsonTaskRepository(self.json_file, self.json_mapper)
        all_tasks = sqlite_repo.get_all()
        json_repo.save_all(all_tasks)

        # Verify JSON repository has the tasks
        all_json_tasks = json_repo.get_all()
        self.assertEqual(len(all_json_tasks), 2)

        json_task1 = json_repo.get_by_id(task1.id)
        json_task2 = json_repo.get_by_id(task2.id)

        self.assertEqual(json_task1.name, "SQLite Task 1")
        self.assertEqual(json_task2.name, "SQLite Task 2")
        self.assertEqual(json_task2.tags, ["rollback"])

        sqlite_repo.close()


if __name__ == "__main__":
    unittest.main()
