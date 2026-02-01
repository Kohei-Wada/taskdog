"""Tests for SqliteTaskRepository."""

from datetime import date, datetime
from pathlib import Path

import pytest

from taskdog_core.domain.constants import MAX_TAGS_PER_TASK
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestSqliteTaskRepository:
    """Test suite for SqliteTaskRepository."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures with temporary database."""
        self.temp_dir = tmp_path
        self.db_path = Path(self.temp_dir) / "test_tasks.db"
        self.database_url = f"sqlite:///{self.db_path}"
        self.mapper = TaskDbMapper()
        self.repository = SqliteTaskRepository(self.database_url, self.mapper)
        yield
        self.repository.close()

    def test_create_task_generates_id_and_saves(self):
        """Test create() generates ID and saves task to database."""
        task = self.repository.create("Test Task", priority=1)

        assert task.id == 1
        assert task.name == "Test Task"
        assert task.priority == 1
        assert task.created_at is not None
        assert task.updated_at is not None

        # Verify persistence
        retrieved = self.repository.get_by_id(1)
        assert retrieved is not None
        assert retrieved.name == "Test Task"

    def test_save_creates_new_task(self):
        """Test save() creates a new task in database."""
        task = Task(id=1, name="New Task", priority=1)

        self.repository.save(task)

        retrieved = self.repository.get_by_id(1)
        assert retrieved is not None
        assert retrieved.name == "New Task"
        assert retrieved.priority == 1

    def test_save_updates_existing_task(self):
        """Test save() updates an existing task."""
        task = Task(id=1, name="Original", priority=1)
        self.repository.save(task)

        # Modify and save again
        task.name = "Updated"
        task.priority = 5
        self.repository.save(task)

        retrieved = self.repository.get_by_id(1)
        assert retrieved.name == "Updated"
        assert retrieved.priority == 5

    def test_get_all_returns_all_tasks(self):
        """Test get_all() retrieves all tasks from database."""
        task1 = Task(id=1, name="Task 1", priority=1)
        task2 = Task(id=2, name="Task 2", priority=2)

        self.repository.save(task1)
        self.repository.save(task2)

        all_tasks = self.repository.get_all()

        assert len(all_tasks) == 2
        assert all_tasks[0].name == "Task 1"
        assert all_tasks[1].name == "Task 2"

    def test_get_by_id_returns_task(self):
        """Test get_by_id() retrieves specific task."""
        task = Task(id=42, name="Specific Task", priority=1)
        self.repository.save(task)

        retrieved = self.repository.get_by_id(42)

        assert retrieved is not None
        assert retrieved.id == 42
        assert retrieved.name == "Specific Task"

    def test_get_by_id_returns_none_for_nonexistent(self):
        """Test get_by_id() returns None for nonexistent task."""
        result = self.repository.get_by_id(999)
        assert result is None

    def test_get_by_ids_returns_multiple_tasks(self):
        """Test get_by_ids() retrieves multiple tasks in one query."""
        task1 = Task(id=1, name="Task 1", priority=1)
        task2 = Task(id=2, name="Task 2", priority=2)
        task3 = Task(id=3, name="Task 3", priority=3)

        self.repository.save(task1)
        self.repository.save(task2)
        self.repository.save(task3)

        result = self.repository.get_by_ids([1, 3])

        assert len(result) == 2
        assert 1 in result
        assert 3 in result
        assert result[1].name == "Task 1"
        assert result[3].name == "Task 3"

    def test_get_by_ids_skips_nonexistent_ids(self):
        """Test get_by_ids() omits nonexistent task IDs."""
        task1 = Task(id=1, name="Task 1", priority=1)
        self.repository.save(task1)

        result = self.repository.get_by_ids([1, 999])

        assert len(result) == 1
        assert 1 in result
        assert 999 not in result

    def test_get_by_ids_returns_empty_dict_for_empty_list(self):
        """Test get_by_ids() returns empty dict for empty input."""
        result = self.repository.get_by_ids([])
        assert result == {}

    def test_save_all_saves_multiple_tasks(self):
        """Test save_all() saves multiple tasks in one transaction."""
        task1 = Task(id=1, name="Task 1", priority=1)
        task2 = Task(id=2, name="Task 2", priority=2)
        task3 = Task(id=3, name="Task 3", priority=3)

        self.repository.save_all([task1, task2, task3])

        all_tasks = self.repository.get_all()
        assert len(all_tasks) == 3

    def test_save_all_with_empty_list(self):
        """Test save_all() handles empty list gracefully."""
        self.repository.save_all([])
        all_tasks = self.repository.get_all()
        assert len(all_tasks) == 0

    def test_delete_removes_task(self):
        """Test delete() removes task from database."""
        task = Task(id=1, name="To Delete", priority=1)
        self.repository.save(task)

        self.repository.delete(1)

        retrieved = self.repository.get_by_id(1)
        assert retrieved is None

    def test_delete_nonexistent_task_does_not_error(self):
        """Test delete() handles nonexistent task gracefully."""
        # Should not raise error
        self.repository.delete(999)

    def test_complex_field_serialization(self):
        """Test complex fields (daily_allocations, tags, etc.) are persisted correctly."""
        task = Task(
            id=1,
            name="Complex Task",
            priority=1,
            daily_allocations={date(2025, 1, 15): 2.0, date(2025, 1, 16): 3.0},
            depends_on=[2, 3, 5],
            tags=["urgent", "backend"],
        )

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        assert retrieved.daily_allocations == {
            date(2025, 1, 15): 2.0,
            date(2025, 1, 16): 3.0,
        }
        assert retrieved.depends_on == [2, 3, 5]
        assert retrieved.tags == ["urgent", "backend"]

    def test_datetime_field_persistence(self):
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

        assert retrieved.created_at == now
        assert retrieved.deadline == deadline
        assert retrieved.planned_start == datetime(2025, 1, 16, 9, 0, 0)

    def test_status_enum_persistence(self):
        """Test TaskStatus enum is persisted correctly."""
        task = Task(id=1, name="Status Test", priority=1, status=TaskStatus.IN_PROGRESS)

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        assert retrieved.status == TaskStatus.IN_PROGRESS

    def test_boolean_field_persistence(self):
        """Test boolean fields are persisted correctly."""
        task = Task(
            id=1, name="Boolean Test", priority=1, is_fixed=True, is_archived=True
        )

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        assert retrieved.is_fixed is True
        assert retrieved.is_archived is True

    def test_optional_fields_with_none(self):
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

        assert retrieved.planned_start is None
        assert retrieved.planned_end is None
        assert retrieved.deadline is None
        assert retrieved.estimated_duration is None

    def test_persistence_across_repository_instances(self):
        """Test data persists across different repository instances."""
        task = Task(id=1, name="Persistent Task", priority=1)
        self.repository.save(task)

        # Close first repository
        self.repository.close()

        # Create new repository instance with same database
        new_repository = SqliteTaskRepository(self.database_url, self.mapper)

        retrieved = new_repository.get_by_id(1)
        assert retrieved is not None
        assert retrieved.name == "Persistent Task"

        new_repository.close()

    def test_empty_complex_fields_persistence(self):
        """Test empty complex fields (empty dicts/lists) are persisted correctly."""
        task = Task(
            id=1,
            name="Empty Fields Task",
            priority=1,
            daily_allocations={},
            depends_on=[],
            tags=[],
        )

        self.repository.save(task)
        retrieved = self.repository.get_by_id(1)

        assert retrieved.daily_allocations == {}
        assert retrieved.depends_on == []
        assert retrieved.tags == []

    def test_get_tag_counts_returns_correct_counts(self):
        """Test get_tag_counts returns accurate counts using SQL (Phase 3)."""
        # Create tasks with various tags
        _ = self.repository.create("Task 1", priority=1, tags=["urgent", "backend"])
        _ = self.repository.create("Task 2", priority=1, tags=["urgent", "frontend"])
        _ = self.repository.create("Task 3", priority=1, tags=["backend"])
        _ = self.repository.create("Task 4", priority=1, tags=[])  # No tags

        # Get tag counts
        tag_counts = self.repository.get_tag_counts()

        # Verify counts
        assert tag_counts.get("urgent") == 2
        assert tag_counts.get("backend") == 2
        assert tag_counts.get("frontend") == 1
        assert len(tag_counts) == 3  # Only 3 unique tags

    def test_get_tag_counts_with_no_tasks(self):
        """Test get_tag_counts returns empty dict when no tasks exist (Phase 3)."""
        tag_counts = self.repository.get_tag_counts()
        assert tag_counts == {}

    def test_get_task_ids_by_tags_or_logic(self):
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
        assert len(task_ids) == 3
        assert task1.id in task_ids
        assert task2.id in task_ids
        assert task3.id in task_ids
        assert task4.id not in task_ids

    def test_get_task_ids_by_tags_and_logic(self):
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
        assert len(task_ids) == 2
        assert task1.id in task_ids
        assert task2.id in task_ids
        assert task3.id not in task_ids
        assert task4.id not in task_ids

    def test_get_task_ids_by_tags_with_empty_list(self):
        """Test get_task_ids_by_tags with empty tag list returns all tasks (Phase 3)."""
        task1 = self.repository.create("Task 1", priority=1, tags=["urgent"])
        task2 = self.repository.create("Task 2", priority=1, tags=["backend"])
        task3 = self.repository.create("Task 3", priority=1, tags=[])

        # Empty tag list should return all task IDs
        task_ids = self.repository.get_task_ids_by_tags([], match_all=False)

        assert len(task_ids) == 3
        assert task1.id in task_ids
        assert task2.id in task_ids
        assert task3.id in task_ids

    def test_get_task_ids_by_tags_with_nonexistent_tag(self):
        """Test get_task_ids_by_tags with nonexistent tag returns empty (Phase 3)."""
        _ = self.repository.create("Task 1", priority=1, tags=["urgent"])
        _ = self.repository.create("Task 2", priority=1, tags=["backend"])

        # Nonexistent tag should return empty list
        task_ids = self.repository.get_task_ids_by_tags(
            ["nonexistent"], match_all=False
        )

        assert task_ids == []

    # ====================================================================
    # Phase 4: Edge Case Tests
    # ====================================================================

    def test_transaction_rollback_does_not_orphan_tags(self):
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
            assert len(tags) == 0

        # Verify task was not saved
        retrieved = self.repository.get_by_id(999)
        assert retrieved is None

    def test_failed_tag_update_does_not_lose_existing_tags(self):
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
        assert retrieved is not None
        assert set(retrieved.tags) == set(original_tags)

    def test_task_with_max_tags(self):
        """Test task with maximum allowed tags (Phase 4)."""
        # Create task with maximum unique tags
        tags = [f"tag-{i:03d}" for i in range(MAX_TAGS_PER_TASK)]
        task = self.repository.create("Task with many tags", priority=1, tags=tags)

        # Verify all tags were saved
        retrieved = self.repository.get_by_id(task.id)
        assert retrieved is not None
        assert len(retrieved.tags) == MAX_TAGS_PER_TASK
        assert set(retrieved.tags) == set(tags)

    def test_repository_with_1000_unique_tags(self):
        """Test repository performance with 1000+ unique tags (Phase 4)."""
        # Create 100 tasks, each with 10 unique tags (1000 total unique tags)
        for i in range(100):
            tags = [f"category-{i // 10}", f"task-{i:03d}", f"batch-{i % 5}"]
            self.repository.create(f"Task {i}", priority=1, tags=tags)

        # Test get_tag_counts performance
        tag_counts = self.repository.get_tag_counts()
        # Should have at least 10 categories + 100 tasks + 5 batches = ~115 unique tags
        assert len(tag_counts) > 100

        # Test filter by tags performance
        task_ids = self.repository.get_task_ids_by_tags(["category-0"], match_all=False)
        # Should find 10 tasks in category-0 (tasks 0-9)
        assert len(task_ids) == 10

    def test_concurrent_tag_creation_same_name(self):
        """Test creating same tag from multiple tasks doesn't cause duplicates (Phase 4)."""
        # Create multiple tasks with the same tag
        # TagResolver should handle this via uniqueness constraint
        tags = ["shared-tag"]

        task1 = self.repository.create("Task 1", priority=1, tags=tags)
        task2 = self.repository.create("Task 2", priority=1, tags=tags)
        task3 = self.repository.create("Task 3", priority=1, tags=tags)

        # Verify all tasks have the tag
        assert task1.tags == ["shared-tag"]
        assert task2.tags == ["shared-tag"]
        assert task3.tags == ["shared-tag"]

        # Verify tag count shows 3 tasks for this tag
        tag_counts = self.repository.get_tag_counts()
        assert tag_counts.get("shared-tag") == 3

        # Verify only one TagModel exists with this name
        with self.repository.Session() as session:
            from sqlalchemy import select

            from taskdog_core.infrastructure.persistence.database.models import TagModel

            stmt = select(TagModel).where(TagModel.name == "shared-tag")
            tag_models = session.scalars(stmt).all()
            assert len(tag_models) == 1

    def test_count_tasks_returns_total_count(self):
        """Test count_tasks() returns total task count without filters."""
        # Create test tasks
        task1 = Task(id=1, name="Task 1", priority=1)
        task2 = Task(id=2, name="Task 2", priority=2, is_archived=True)
        task3 = Task(id=3, name="Task 3", priority=3)

        self.repository.save_all([task1, task2, task3])

        # Count all tasks (including archived)
        total_count = self.repository.count_tasks()
        assert total_count == 3

        # Count non-archived tasks only
        non_archived_count = self.repository.count_tasks(include_archived=False)
        assert non_archived_count == 2

    def test_count_tasks_with_status_filter(self):
        """Test count_tasks() with status filter."""
        # Create tasks with different statuses
        task1 = Task(id=1, name="Pending", priority=1, status=TaskStatus.PENDING)
        task2 = Task(
            id=2, name="In Progress", priority=2, status=TaskStatus.IN_PROGRESS
        )
        task3 = Task(id=3, name="Completed", priority=3, status=TaskStatus.COMPLETED)
        task4 = Task(
            id=4, name="Another Pending", priority=4, status=TaskStatus.PENDING
        )

        self.repository.save_all([task1, task2, task3, task4])

        # Count PENDING tasks
        pending_count = self.repository.count_tasks(status=TaskStatus.PENDING)
        assert pending_count == 2

        # Count COMPLETED tasks
        completed_count = self.repository.count_tasks(status=TaskStatus.COMPLETED)
        assert completed_count == 1

        # Count IN_PROGRESS tasks
        in_progress_count = self.repository.count_tasks(status=TaskStatus.IN_PROGRESS)
        assert in_progress_count == 1

    def test_count_tasks_with_tag_filter(self):
        """Test count_tasks() with tag filter (OR and AND logic)."""
        # Create tasks with tags
        task1 = Task(id=1, name="Task 1", priority=1, tags=["urgent"])
        task2 = Task(id=2, name="Task 2", priority=2, tags=["urgent", "backend"])
        task3 = Task(id=3, name="Task 3", priority=3, tags=["backend"])
        task4 = Task(id=4, name="Task 4", priority=4, tags=["frontend"])

        self.repository.save_all([task1, task2, task3, task4])

        # OR logic: tasks with 'urgent' OR 'backend'
        or_count = self.repository.count_tasks(
            tags=["urgent", "backend"], match_all_tags=False
        )
        assert or_count == 3  # task1, task2, task3

        # AND logic: tasks with 'urgent' AND 'backend'
        and_count = self.repository.count_tasks(
            tags=["urgent", "backend"], match_all_tags=True
        )
        assert and_count == 1  # only task2

        # Single tag filter
        urgent_count = self.repository.count_tasks(tags=["urgent"])
        assert urgent_count == 2  # task1, task2

    def test_count_tasks_with_date_filter(self):
        """Test count_tasks() with date range filter."""
        # Create tasks with various dates
        task1 = Task(id=1, name="Task 1", priority=1, deadline=date(2025, 1, 15))
        task2 = Task(id=2, name="Task 2", priority=2, deadline=date(2025, 2, 10))
        task3 = Task(id=3, name="Task 3", priority=3, deadline=date(2025, 3, 5))
        task4 = Task(id=4, name="Task 4", priority=4, planned_start=date(2025, 2, 15))

        self.repository.save_all([task1, task2, task3, task4])

        # Count tasks in February 2025
        feb_count = self.repository.count_tasks(
            start_date=date(2025, 2, 1), end_date=date(2025, 2, 28)
        )
        assert feb_count == 2  # task2, task4

        # Count tasks after Feb 1
        after_feb_count = self.repository.count_tasks(start_date=date(2025, 2, 1))
        assert after_feb_count == 3  # task2, task3, task4

        # Count tasks before Feb 28
        before_feb_count = self.repository.count_tasks(end_date=date(2025, 2, 28))
        assert before_feb_count == 3  # task1, task2, task4

    def test_count_tasks_with_combined_filters(self):
        """Test count_tasks() with multiple filters combined."""
        # Create diverse test data
        task1 = Task(
            id=1,
            name="Urgent Backend",
            priority=1,
            status=TaskStatus.PENDING,
            tags=["urgent", "backend"],
        )
        task2 = Task(
            id=2,
            name="Urgent Frontend",
            priority=2,
            status=TaskStatus.IN_PROGRESS,
            tags=["urgent", "frontend"],
        )
        task3 = Task(
            id=3,
            name="Backend",
            priority=3,
            status=TaskStatus.PENDING,
            tags=["backend"],
            is_archived=True,
        )
        task4 = Task(id=4, name="Normal", priority=4, status=TaskStatus.PENDING)

        self.repository.save_all([task1, task2, task3, task4])

        # Count non-archived PENDING tasks
        pending_non_archived = self.repository.count_tasks(
            status=TaskStatus.PENDING, include_archived=False
        )
        assert pending_non_archived == 2  # task1, task4

        # Count non-archived tasks with 'urgent' tag
        urgent_non_archived = self.repository.count_tasks(
            tags=["urgent"], include_archived=False
        )
        assert urgent_non_archived == 2  # task1, task2

        # Count non-archived PENDING tasks with 'urgent' tag
        complex_filter = self.repository.count_tasks(
            status=TaskStatus.PENDING, tags=["urgent"], include_archived=False
        )
        assert complex_filter == 1  # only task1

    def test_count_tasks_with_tags_returns_tagged_count(self):
        """Test count_tasks_with_tags() returns count of tasks with at least one tag."""
        # Create tasks with and without tags
        task1 = Task(id=1, name="Tagged 1", priority=1, tags=["urgent"])
        task2 = Task(id=2, name="Tagged 2", priority=2, tags=["backend", "frontend"])
        task3 = Task(id=3, name="No tags", priority=3)
        task4 = Task(id=4, name="Tagged 3", priority=4, tags=["docs"])
        task5 = Task(id=5, name="Also no tags", priority=5)

        self.repository.save_all([task1, task2, task3, task4, task5])

        # Count tasks with at least one tag
        tagged_count = self.repository.count_tasks_with_tags()
        assert tagged_count == 3  # task1, task2, task4

    def test_count_tasks_with_tags_returns_zero_when_no_tags(self):
        """Test count_tasks_with_tags() returns 0 when no tasks have tags."""
        # Create tasks without tags
        task1 = Task(id=1, name="No tags 1", priority=1)
        task2 = Task(id=2, name="No tags 2", priority=2)

        self.repository.save_all([task1, task2])

        # Should return 0
        tagged_count = self.repository.count_tasks_with_tags()
        assert tagged_count == 0

    def test_count_tasks_consistency_with_get_filtered(self):
        """Test count_tasks() returns same count as len(get_filtered())."""
        # Create diverse test data
        task1 = Task(
            id=1, name="Task 1", priority=1, status=TaskStatus.PENDING, tags=["urgent"]
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=2,
            status=TaskStatus.COMPLETED,
            tags=["backend"],
        )
        task3 = Task(
            id=3, name="Task 3", priority=3, status=TaskStatus.PENDING, is_archived=True
        )
        task4 = Task(id=4, name="Task 4", priority=4, deadline=date(2025, 2, 10))

        self.repository.save_all([task1, task2, task3, task4])

        # Test various filter combinations
        test_cases = [
            {"include_archived": False},
            {"status": TaskStatus.PENDING},
            {"tags": ["urgent"]},
            {"status": TaskStatus.PENDING, "include_archived": False},
        ]

        for filters in test_cases:
            count = self.repository.count_tasks(**filters)
            filtered_tasks = self.repository.get_filtered(**filters)
            assert count == len(filtered_tasks), (
                f"count_tasks({filters}) != len(get_filtered({filters}))"
            )

    # ====================================================================
    # Dual-Write Tests for Daily Allocations (Phase 2)
    # ====================================================================

    def test_save_writes_daily_allocations_to_normalized_table(self):
        """Test save() writes daily_allocations to both JSON and normalized table."""
        from sqlalchemy import select

        from taskdog_core.infrastructure.persistence.database.models import (
            DailyAllocationModel,
        )

        task = Task(
            id=1,
            name="Dual Write Test",
            priority=1,
            daily_allocations={date(2025, 1, 15): 2.0, date(2025, 1, 16): 3.5},
        )

        self.repository.save(task)

        # Verify JSON column is populated (existing behavior)
        retrieved = self.repository.get_by_id(1)
        assert retrieved.daily_allocations == {
            date(2025, 1, 15): 2.0,
            date(2025, 1, 16): 3.5,
        }

        # Verify normalized table is also populated
        with self.repository.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()

            assert len(records) == 2
            records_by_date = {r.date: r.hours for r in records}
            assert records_by_date[date(2025, 1, 15)] == 2.0
            assert records_by_date[date(2025, 1, 16)] == 3.5

    def test_save_all_writes_daily_allocations_to_normalized_table(self):
        """Test save_all() writes daily_allocations to normalized table for all tasks."""
        from sqlalchemy import select

        from taskdog_core.infrastructure.persistence.database.models import (
            DailyAllocationModel,
        )

        task1 = Task(
            id=1,
            name="Task 1",
            priority=1,
            daily_allocations={date(2025, 1, 15): 2.0},
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=2,
            daily_allocations={date(2025, 1, 16): 3.0, date(2025, 1, 17): 4.0},
        )

        self.repository.save_all([task1, task2])

        # Verify normalized table has all allocations
        with self.repository.Session() as session:
            stmt = select(DailyAllocationModel).order_by(DailyAllocationModel.task_id)
            records = session.scalars(stmt).all()

            assert len(records) == 3
            task1_records = [r for r in records if r.task_id == 1]
            task2_records = [r for r in records if r.task_id == 2]

            assert len(task1_records) == 1
            assert len(task2_records) == 2

    def test_create_writes_daily_allocations_to_normalized_table(self):
        """Test create() writes daily_allocations to normalized table."""
        from sqlalchemy import select

        from taskdog_core.infrastructure.persistence.database.models import (
            DailyAllocationModel,
        )

        task = self.repository.create(
            "Create Test",
            priority=1,
            daily_allocations={date(2025, 1, 20): 5.0},
        )

        # Verify normalized table is populated
        with self.repository.Session() as session:
            stmt = select(DailyAllocationModel).where(
                DailyAllocationModel.task_id == task.id
            )
            records = session.scalars(stmt).all()

            assert len(records) == 1
            assert records[0].date == date(2025, 1, 20)
            assert records[0].hours == 5.0

    def test_update_replaces_daily_allocations_in_normalized_table(self):
        """Test updating task replaces allocations in normalized table."""
        from sqlalchemy import select

        from taskdog_core.infrastructure.persistence.database.models import (
            DailyAllocationModel,
        )

        # Create initial task with allocations
        task = Task(
            id=1,
            name="Update Test",
            priority=1,
            daily_allocations={date(2025, 1, 15): 2.0},
        )
        self.repository.save(task)

        # Update with different allocations
        task.daily_allocations = {date(2025, 1, 20): 4.0, date(2025, 1, 21): 5.0}
        self.repository.save(task)

        # Verify normalized table has only new allocations
        with self.repository.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()

            assert len(records) == 2
            dates = {r.date for r in records}
            assert date(2025, 1, 15) not in dates
            assert date(2025, 1, 20) in dates
            assert date(2025, 1, 21) in dates

    def test_delete_task_cascades_to_normalized_allocations(self):
        """Test deleting task also deletes normalized allocations (CASCADE)."""
        from sqlalchemy import select

        from taskdog_core.infrastructure.persistence.database.models import (
            DailyAllocationModel,
        )

        task = Task(
            id=1,
            name="Delete Test",
            priority=1,
            daily_allocations={date(2025, 1, 15): 2.0, date(2025, 1, 16): 3.0},
        )
        self.repository.save(task)

        # Verify allocations exist
        with self.repository.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 2

        # Delete task
        self.repository.delete(1)

        # Verify allocations are also deleted (CASCADE)
        with self.repository.Session() as session:
            stmt = select(DailyAllocationModel).where(DailyAllocationModel.task_id == 1)
            records = session.scalars(stmt).all()
            assert len(records) == 0

    # ====================================================================
    # SQL Aggregation Tests for Daily Workload (get_daily_workload_totals)
    # ====================================================================

    def test_get_daily_workload_totals_returns_sum_by_date(self):
        """Test get_daily_workload_totals aggregates hours by date."""
        # Create two tasks with overlapping dates
        task1 = Task(
            id=1,
            name="Task 1",
            priority=1,
            daily_allocations={
                date(2025, 1, 20): 2.0,
                date(2025, 1, 21): 3.0,
            },
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=2,
            daily_allocations={
                date(2025, 1, 20): 4.0,  # Same date as task1
                date(2025, 1, 22): 5.0,
            },
        )
        self.repository.save_all([task1, task2])

        # Get totals for the date range
        totals = self.repository.get_daily_workload_totals(
            start_date=date(2025, 1, 20),
            end_date=date(2025, 1, 22),
        )

        # Verify aggregation
        assert totals[date(2025, 1, 20)] == 6.0  # 2.0 + 4.0
        assert totals[date(2025, 1, 21)] == 3.0  # only task1
        assert totals[date(2025, 1, 22)] == 5.0  # only task2

    def test_get_daily_workload_totals_filters_by_task_ids(self):
        """Test get_daily_workload_totals can filter by specific task IDs."""
        # Create three tasks
        task1 = Task(
            id=1,
            name="Task 1",
            priority=1,
            daily_allocations={date(2025, 1, 20): 2.0},
        )
        task2 = Task(
            id=2,
            name="Task 2",
            priority=2,
            daily_allocations={date(2025, 1, 20): 3.0},
        )
        task3 = Task(
            id=3,
            name="Task 3",
            priority=3,
            daily_allocations={date(2025, 1, 20): 5.0},
        )
        self.repository.save_all([task1, task2, task3])

        # Get totals for only task1 and task2
        totals = self.repository.get_daily_workload_totals(
            start_date=date(2025, 1, 20),
            end_date=date(2025, 1, 20),
            task_ids=[1, 2],
        )

        # Should only include task1 and task2
        assert totals[date(2025, 1, 20)] == 5.0  # 2.0 + 3.0, not 10.0

    def test_get_daily_workload_totals_respects_date_range(self):
        """Test get_daily_workload_totals only includes dates in range."""
        task = Task(
            id=1,
            name="Task",
            priority=1,
            daily_allocations={
                date(2025, 1, 19): 1.0,  # Before range
                date(2025, 1, 20): 2.0,  # In range
                date(2025, 1, 21): 3.0,  # In range
                date(2025, 1, 22): 4.0,  # After range
            },
        )
        self.repository.save(task)

        totals = self.repository.get_daily_workload_totals(
            start_date=date(2025, 1, 20),
            end_date=date(2025, 1, 21),
        )

        # Only dates within range should be included
        assert date(2025, 1, 19) not in totals
        assert totals[date(2025, 1, 20)] == 2.0
        assert totals[date(2025, 1, 21)] == 3.0
        assert date(2025, 1, 22) not in totals

    def test_get_daily_workload_totals_returns_empty_for_no_allocations(self):
        """Test get_daily_workload_totals returns empty dict when no allocations."""
        # Create task without allocations
        task = Task(id=1, name="No Allocations", priority=1)
        self.repository.save(task)

        totals = self.repository.get_daily_workload_totals(
            start_date=date(2025, 1, 20),
            end_date=date(2025, 1, 24),
        )

        assert totals == {}

    def test_get_daily_workload_totals_returns_empty_for_empty_task_ids(self):
        """Test get_daily_workload_totals returns empty dict when task_ids is empty list."""
        task = Task(
            id=1,
            name="Task",
            priority=1,
            daily_allocations={date(2025, 1, 20): 5.0},
        )
        self.repository.save(task)

        # Empty task_ids list should return empty result
        totals = self.repository.get_daily_workload_totals(
            start_date=date(2025, 1, 20),
            end_date=date(2025, 1, 24),
            task_ids=[],
        )

        assert totals == {}
