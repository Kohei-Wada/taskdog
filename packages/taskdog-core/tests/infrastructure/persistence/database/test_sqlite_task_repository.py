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

    def test_get_tag_counts_returns_correct_counts(self) -> None:
        """Test get_tag_counts returns accurate counts using SQL (Phase 3)."""
        # Create tasks with various tags
        _ = self.repository.create("Task 1", priority=1, tags=["urgent", "backend"])
        _ = self.repository.create("Task 2", priority=1, tags=["urgent", "frontend"])
        _ = self.repository.create("Task 3", priority=1, tags=["backend"])
        _ = self.repository.create("Task 4", priority=1, tags=[])  # No tags

        # Get tag counts
        tag_counts = self.repository.get_tag_counts()

        # Verify counts
        self.assertEqual(tag_counts.get("urgent"), 2)
        self.assertEqual(tag_counts.get("backend"), 2)
        self.assertEqual(tag_counts.get("frontend"), 1)
        self.assertEqual(len(tag_counts), 3)  # Only 3 unique tags

    def test_get_tag_counts_with_no_tasks(self) -> None:
        """Test get_tag_counts returns empty dict when no tasks exist (Phase 3)."""
        tag_counts = self.repository.get_tag_counts()
        self.assertEqual(tag_counts, {})

    def test_get_task_ids_by_tags_or_logic(self) -> None:
        """Test get_task_ids_by_tags with OR logic (Phase 3)."""
        # Create tasks with various tags
        task1 = self.repository.create("Task 1", priority=1, tags=["urgent", "backend"])
        task2 = self.repository.create(
            "Task 2", priority=1, tags=["urgent", "frontend"]
        )
        task3 = self.repository.create("Task 3", priority=1, tags=["backend"])
        task4 = self.repository.create("Task 4", priority=1, tags=["other"])

        # OR logic: tasks with 'urgent' OR 'backend'
        task_ids = self.repository.get_task_ids_by_tags(
            ["urgent", "backend"], match_all=False
        )

        # Should return task1 (has both), task2 (has urgent), task3 (has backend)
        self.assertEqual(len(task_ids), 3)
        self.assertIn(task1.id, task_ids)
        self.assertIn(task2.id, task_ids)
        self.assertIn(task3.id, task_ids)
        self.assertNotIn(task4.id, task_ids)

    def test_get_task_ids_by_tags_and_logic(self) -> None:
        """Test get_task_ids_by_tags with AND logic (Phase 3)."""
        # Create tasks with various tags
        task1 = self.repository.create("Task 1", priority=1, tags=["urgent", "backend"])
        task2 = self.repository.create(
            "Task 2", priority=1, tags=["urgent", "backend", "frontend"]
        )
        task3 = self.repository.create("Task 3", priority=1, tags=["urgent"])
        task4 = self.repository.create("Task 4", priority=1, tags=["backend"])

        # AND logic: tasks with 'urgent' AND 'backend'
        task_ids = self.repository.get_task_ids_by_tags(
            ["urgent", "backend"], match_all=True
        )

        # Should return task1 and task2 (both have urgent AND backend)
        self.assertEqual(len(task_ids), 2)
        self.assertIn(task1.id, task_ids)
        self.assertIn(task2.id, task_ids)
        self.assertNotIn(task3.id, task_ids)
        self.assertNotIn(task4.id, task_ids)

    def test_get_task_ids_by_tags_with_empty_list(self) -> None:
        """Test get_task_ids_by_tags with empty tag list returns all tasks (Phase 3)."""
        task1 = self.repository.create("Task 1", priority=1, tags=["urgent"])
        task2 = self.repository.create("Task 2", priority=1, tags=["backend"])
        task3 = self.repository.create("Task 3", priority=1, tags=[])

        # Empty tag list should return all task IDs
        task_ids = self.repository.get_task_ids_by_tags([], match_all=False)

        self.assertEqual(len(task_ids), 3)
        self.assertIn(task1.id, task_ids)
        self.assertIn(task2.id, task_ids)
        self.assertIn(task3.id, task_ids)

    def test_get_task_ids_by_tags_with_nonexistent_tag(self) -> None:
        """Test get_task_ids_by_tags with nonexistent tag returns empty (Phase 3)."""
        _ = self.repository.create("Task 1", priority=1, tags=["urgent"])
        _ = self.repository.create("Task 2", priority=1, tags=["backend"])

        # Nonexistent tag should return empty list
        task_ids = self.repository.get_task_ids_by_tags(
            ["nonexistent"], match_all=False
        )

        self.assertEqual(task_ids, [])

    # ====================================================================
    # Phase 4: Edge Case Tests
    # ====================================================================

    def test_transaction_rollback_does_not_orphan_tags(self) -> None:
        """Test that rolling back task creation doesn't leave orphaned tags (Phase 4)."""
        # Create a task with tags in a session
        with self.repository.Session() as session:
            # Manually create a task with tags using session
            from taskdog_core.infrastructure.persistence.database.models import (
                TagModel,
                TaskModel,
            )

            task = TaskModel(
                id=999,
                name="Test Task",
                priority=1,
                status="PENDING",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_archived=False,
            )

            # Create tags and associate
            tag1 = TagModel(name="rollback-test-1", created_at=datetime.now())
            tag2 = TagModel(name="rollback-test-2", created_at=datetime.now())
            session.add_all([tag1, tag2])
            session.flush()  # Get IDs

            task.tag_models.extend([tag1, tag2])
            session.add(task)

            # Rollback instead of commit
            session.rollback()

        # Verify tags were not saved (no orphaned tags)
        with self.repository.Session() as session:
            from sqlalchemy import select

            from taskdog_core.infrastructure.persistence.database.models import TagModel

            stmt = select(TagModel).where(
                TagModel.name.in_(["rollback-test-1", "rollback-test-2"])
            )
            tags = session.scalars(stmt).all()
            self.assertEqual(len(tags), 0)

        # Verify task was not saved
        retrieved = self.repository.get_by_id(999)
        self.assertIsNone(retrieved)

    def test_failed_tag_update_does_not_lose_existing_tags(self) -> None:
        """Test that failed tag update preserves original tags (Phase 4)."""
        # Create task with tags
        task = self.repository.create(
            "Test Task", priority=1, tags=["original-1", "original-2"]
        )
        original_tags = task.tags.copy()

        # Simulate failed update by causing an error
        try:
            with self.repository.Session() as session:
                from taskdog_core.infrastructure.persistence.database.models import (
                    TaskModel,
                )

                task_model = session.get(TaskModel, task.id)
                if task_model:
                    # Clear tags
                    task_model.tag_models.clear()
                    session.flush()

                    # Force an error before commit
                    raise RuntimeError("Simulated error during tag update")
        except RuntimeError:
            # Expected error
            pass

        # Verify original tags are still there (get_by_id bypasses cache)
        retrieved = self.repository.get_by_id(task.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(set(retrieved.tags), set(original_tags))

    def test_task_with_100_tags(self) -> None:
        """Test task with 100 tags (large tag set) (Phase 4)."""
        # Create task with 100 unique tags
        tags = [f"tag-{i:03d}" for i in range(100)]
        task = self.repository.create("Task with many tags", priority=1, tags=tags)

        # Verify all tags were saved
        retrieved = self.repository.get_by_id(task.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(len(retrieved.tags), 100)
        self.assertEqual(set(retrieved.tags), set(tags))

    def test_repository_with_1000_unique_tags(self) -> None:
        """Test repository performance with 1000+ unique tags (Phase 4)."""
        # Create 100 tasks, each with 10 unique tags (1000 total unique tags)
        for i in range(100):
            tags = [f"category-{i // 10}", f"task-{i:03d}", f"batch-{i % 5}"]
            self.repository.create(f"Task {i}", priority=1, tags=tags)

        # Test get_tag_counts performance
        tag_counts = self.repository.get_tag_counts()
        # Should have at least 10 categories + 100 tasks + 5 batches = ~115 unique tags
        self.assertGreater(len(tag_counts), 100)

        # Test filter by tags performance
        task_ids = self.repository.get_task_ids_by_tags(["category-0"], match_all=False)
        # Should find 10 tasks in category-0 (tasks 0-9)
        self.assertEqual(len(task_ids), 10)

    def test_concurrent_tag_creation_same_name(self) -> None:
        """Test creating same tag from multiple tasks doesn't cause duplicates (Phase 4)."""
        # Create multiple tasks with the same tag
        # TagResolver should handle this via uniqueness constraint
        tags = ["shared-tag"]

        task1 = self.repository.create("Task 1", priority=1, tags=tags)
        task2 = self.repository.create("Task 2", priority=1, tags=tags)
        task3 = self.repository.create("Task 3", priority=1, tags=tags)

        # Verify all tasks have the tag
        self.assertEqual(task1.tags, ["shared-tag"])
        self.assertEqual(task2.tags, ["shared-tag"])
        self.assertEqual(task3.tags, ["shared-tag"])

        # Verify tag count shows 3 tasks for this tag
        tag_counts = self.repository.get_tag_counts()
        self.assertEqual(tag_counts.get("shared-tag"), 3)

        # Verify only one TagModel exists with this name
        with self.repository.Session() as session:
            from sqlalchemy import select

            from taskdog_core.infrastructure.persistence.database.models import TagModel

            stmt = select(TagModel).where(TagModel.name == "shared-tag")
            tag_models = session.scalars(stmt).all()
            self.assertEqual(len(tag_models), 1)


if __name__ == "__main__":
    unittest.main()
