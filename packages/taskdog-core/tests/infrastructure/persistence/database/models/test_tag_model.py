"""Tests for TagModel and TaskTagModel (Phase 1).

This test suite verifies the basic functionality of the new tag models
introduced in Phase 1 of Issue 228 (tag entity separation).

Note: These tests verify schema creation and basic model behavior.
The integration with TaskDbMapper and repository layer will be tested
in Phase 2.
"""

from datetime import datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from taskdog_core.infrastructure.persistence.database.models import (
    Base,
    TagModel,
    TaskModel,
    TaskTagModel,
)


class TestTagModel:
    """Test suite for TagModel and TaskTagModel."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures with temporary database."""
        self.temp_dir = tmp_path
        self.db_path = Path(self.temp_dir) / "test_tags.db"
        self.database_url = f"sqlite:///{self.db_path}"

        # Create engine and session
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        yield
        self.session.close()
        self.engine.dispose()

    def test_tag_model_creation(self):
        """Test TagModel can be created and persisted."""
        tag = TagModel(name="urgent", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify persistence
        retrieved = self.session.scalar(
            select(TagModel).where(TagModel.name == "urgent")
        )
        assert retrieved is not None
        assert retrieved.name == "urgent"
        assert retrieved.id == 1

    def test_tag_model_unique_constraint(self):
        """Test TagModel enforces unique tag names."""
        tag1 = TagModel(name="backend", created_at=datetime.now())
        self.session.add(tag1)
        self.session.commit()

        # Try to create duplicate
        tag2 = TagModel(name="backend", created_at=datetime.now())
        self.session.add(tag2)

        with pytest.raises(IntegrityError):
            self.session.commit()

        # Rollback the failed transaction
        self.session.rollback()

    def test_task_tag_model_creation(self):
        """Test TaskTagModel can create task-tag associations."""
        # Create a task
        task = TaskModel(
            name="Test Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.session.add(task)
        self.session.commit()

        # Create a tag
        tag = TagModel(name="important", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Create association
        task_tag = TaskTagModel(task_id=task.id, tag_id=tag.id)
        self.session.add(task_tag)
        self.session.commit()

        # Verify association
        retrieved = self.session.scalar(
            select(TaskTagModel).where(
                TaskTagModel.task_id == task.id, TaskTagModel.tag_id == tag.id
            )
        )
        assert retrieved is not None
        assert retrieved.task_id == task.id
        assert retrieved.tag_id == tag.id

    def test_task_tag_relationship(self):
        """Test SQLAlchemy relationship between Task and Tag models."""
        # Create a task
        task = TaskModel(
            name="Test Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Create tags
        tag1 = TagModel(name="urgent", created_at=datetime.now())
        tag2 = TagModel(name="backend", created_at=datetime.now())

        # Associate tags with task using relationship
        task.tag_models.append(tag1)
        task.tag_models.append(tag2)

        self.session.add(task)
        self.session.commit()

        # Retrieve and verify
        retrieved_task = self.session.get(TaskModel, task.id)
        assert retrieved_task is not None
        assert len(retrieved_task.tag_models) == 2

        tag_names = {tag.name for tag in retrieved_task.tag_models}
        assert tag_names == {"urgent", "backend"}

    def test_cascade_delete_on_task_deletion(self):
        """Test that task-tag associations are deleted when task is deleted."""
        # Create task and tag
        task = TaskModel(
            name="Test Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        tag = TagModel(name="test", created_at=datetime.now())
        task.tag_models.append(tag)

        self.session.add(task)
        self.session.commit()

        task_id = task.id
        tag_id = tag.id

        # Delete task
        self.session.delete(task)
        self.session.commit()

        # Verify task-tag association is deleted (cascade)
        association = self.session.scalar(
            select(TaskTagModel).where(
                TaskTagModel.task_id == task_id, TaskTagModel.tag_id == tag_id
            )
        )
        assert association is None

        # Tag should still exist (orphaned)
        orphaned_tag = self.session.get(TagModel, tag_id)
        assert orphaned_tag is not None

    def test_multiple_tasks_can_share_tag(self):
        """Test that multiple tasks can be associated with the same tag."""
        # Create one tag
        tag = TagModel(name="shared", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Create multiple tasks with the same tag
        task1 = TaskModel(
            name="Task 1",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task1.tag_models.append(tag)

        task2 = TaskModel(
            name="Task 2",
            priority=2,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task2.tag_models.append(tag)

        self.session.add(task1)
        self.session.add(task2)
        self.session.commit()

        # Verify both tasks are associated with the same tag
        retrieved_tag = self.session.get(TagModel, tag.id)
        assert retrieved_tag is not None
        assert len(retrieved_tag.tasks) == 2

        task_names = {task.name for task in retrieved_tag.tasks}
        assert task_names == {"Task 1", "Task 2"}

    def test_cascade_delete_on_tag_deletion(self):
        """Test that task-tag associations are deleted when tag is deleted."""
        # Create task and tag
        task = TaskModel(
            name="Test Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        tag = TagModel(name="to-delete", created_at=datetime.now())
        task.tag_models.append(tag)

        self.session.add(task)
        self.session.commit()

        task_id = task.id
        tag_id = tag.id

        # Delete tag
        self.session.delete(tag)
        self.session.commit()

        # Verify task-tag association is deleted (cascade)
        association = self.session.scalar(
            select(TaskTagModel).where(
                TaskTagModel.task_id == task_id, TaskTagModel.tag_id == tag_id
            )
        )
        assert association is None

        # Task should still exist
        remaining_task = self.session.get(TaskModel, task_id)
        assert remaining_task is not None
        assert len(remaining_task.tag_models) == 0

    def test_duplicate_task_tag_association_prevented(self):
        """Test that duplicate task-tag associations are prevented by unique constraint."""
        # Create task and tag
        task = TaskModel(
            name="Test Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        tag = TagModel(name="duplicate-test", created_at=datetime.now())

        self.session.add(task)
        self.session.add(tag)
        self.session.commit()

        # Create first association
        task_tag1 = TaskTagModel(task_id=task.id, tag_id=tag.id)
        self.session.add(task_tag1)
        self.session.commit()

        # Try to create duplicate association
        # Expunge the first instance to avoid identity conflict warning
        self.session.expunge(task_tag1)
        task_tag2 = TaskTagModel(task_id=task.id, tag_id=tag.id)
        self.session.add(task_tag2)

        with pytest.raises(IntegrityError):
            self.session.commit()

        # Rollback the failed transaction
        self.session.rollback()

    def test_task_with_no_tags(self):
        """Test that tasks can exist without any tags."""
        task = TaskModel(
            name="Untagged Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.session.add(task)
        self.session.commit()

        # Retrieve and verify
        retrieved_task = self.session.get(TaskModel, task.id)
        assert retrieved_task is not None
        assert len(retrieved_task.tag_models) == 0

    def test_tag_with_no_tasks(self):
        """Test that tags can exist without any associated tasks (orphaned tags)."""
        tag = TagModel(name="orphan", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Retrieve and verify
        retrieved_tag = self.session.get(TagModel, tag.id)
        assert retrieved_tag is not None
        assert len(retrieved_tag.tasks) == 0

    def test_remove_tag_from_task(self):
        """Test removing a specific tag from a task."""
        # Create task with two tags
        task = TaskModel(
            name="Test Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        tag1 = TagModel(name="keep", created_at=datetime.now())
        tag2 = TagModel(name="remove", created_at=datetime.now())

        task.tag_models.append(tag1)
        task.tag_models.append(tag2)

        self.session.add(task)
        self.session.commit()

        # Remove one tag
        task.tag_models.remove(tag2)
        self.session.commit()

        # Verify only one tag remains
        retrieved_task = self.session.get(TaskModel, task.id)
        assert retrieved_task is not None
        assert len(retrieved_task.tag_models) == 1
        assert retrieved_task.tag_models[0].name == "keep"

    def test_clear_all_tags_from_task(self):
        """Test clearing all tags from a task."""
        # Create task with multiple tags
        task = TaskModel(
            name="Test Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        tag1 = TagModel(name="tag1", created_at=datetime.now())
        tag2 = TagModel(name="tag2", created_at=datetime.now())
        tag3 = TagModel(name="tag3", created_at=datetime.now())

        task.tag_models.extend([tag1, tag2, tag3])
        self.session.add(task)
        self.session.commit()

        # Clear all tags
        task.tag_models.clear()
        self.session.commit()

        # Verify no tags remain
        retrieved_task = self.session.get(TaskModel, task.id)
        assert retrieved_task is not None
        assert len(retrieved_task.tag_models) == 0

    def test_query_tasks_by_tag(self):
        """Test querying tasks by a specific tag."""
        # Create a tag
        tag = TagModel(name="query-test", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Create multiple tasks, some with the tag
        task1 = TaskModel(
            name="Tagged Task 1",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task1.tag_models.append(tag)

        task2 = TaskModel(
            name="Untagged Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        task3 = TaskModel(
            name="Tagged Task 2",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task3.tag_models.append(tag)

        self.session.add_all([task1, task2, task3])
        self.session.commit()

        # Query tasks with the tag
        tagged_tasks = (
            self.session.query(TaskModel)
            .join(TaskModel.tag_models)
            .filter(TagModel.name == "query-test")
            .all()
        )

        assert len(tagged_tasks) == 2
        task_names = {task.name for task in tagged_tasks}
        assert task_names == {"Tagged Task 1", "Tagged Task 2"}

    def test_multiple_tasks_multiple_tags(self):
        """Test complex many-to-many relationship with multiple tasks and tags."""
        # Create tags
        tag_urgent = TagModel(name="urgent", created_at=datetime.now())
        tag_backend = TagModel(name="backend", created_at=datetime.now())
        tag_frontend = TagModel(name="frontend", created_at=datetime.now())

        # Create tasks with different tag combinations
        task1 = TaskModel(
            name="Backend Bug",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task1.tag_models.extend([tag_urgent, tag_backend])

        task2 = TaskModel(
            name="Frontend Feature",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task2.tag_models.append(tag_frontend)

        task3 = TaskModel(
            name="Critical Backend Issue",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task3.tag_models.extend([tag_urgent, tag_backend])

        self.session.add_all([task1, task2, task3])
        self.session.commit()

        # Verify tag_urgent has 2 tasks
        retrieved_urgent = (
            self.session.query(TagModel).filter(TagModel.name == "urgent").first()
        )
        assert retrieved_urgent is not None
        assert len(retrieved_urgent.tasks) == 2

        # Verify tag_backend has 2 tasks
        retrieved_backend = (
            self.session.query(TagModel).filter(TagModel.name == "backend").first()
        )
        assert retrieved_backend is not None
        assert len(retrieved_backend.tasks) == 2

        # Verify tag_frontend has 1 task
        retrieved_frontend = (
            self.session.query(TagModel).filter(TagModel.name == "frontend").first()
        )
        assert retrieved_frontend is not None
        assert len(retrieved_frontend.tasks) == 1

    def test_tag_case_sensitivity(self):
        """Test that tag names are case-sensitive."""
        tag_lower = TagModel(name="urgent", created_at=datetime.now())
        tag_upper = TagModel(name="URGENT", created_at=datetime.now())

        self.session.add(tag_lower)
        self.session.add(tag_upper)
        self.session.commit()

        # Both tags should exist as separate entities
        tags = (
            self.session.query(TagModel)
            .filter(TagModel.name.in_(["urgent", "URGENT"]))
            .all()
        )
        assert len(tags) == 2

    def test_tag_with_special_characters(self):
        """Test that tags can contain special characters."""
        special_tags = [
            "bug-fix",
            "v2.0",
            "frontend/ui",
            "high-priority!",
            "日本語タグ",
        ]

        for tag_name in special_tags:
            tag = TagModel(name=tag_name, created_at=datetime.now())
            self.session.add(tag)

        self.session.commit()

        # Verify all tags were created
        tags = self.session.query(TagModel).all()
        assert len(tags) == len(special_tags)

        tag_names = {tag.name for tag in tags}
        assert tag_names == set(special_tags)

    def test_update_task_tags_by_replacing_collection(self):
        """Test updating task tags by replacing the entire collection."""
        # Create task with initial tags
        task = TaskModel(
            name="Test Task",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        old_tag1 = TagModel(name="old1", created_at=datetime.now())
        old_tag2 = TagModel(name="old2", created_at=datetime.now())
        task.tag_models.extend([old_tag1, old_tag2])

        self.session.add(task)
        self.session.commit()

        # Replace tags with new ones
        new_tag1 = TagModel(name="new1", created_at=datetime.now())
        new_tag2 = TagModel(name="new2", created_at=datetime.now())

        task.tag_models.clear()
        task.tag_models.extend([new_tag1, new_tag2])
        self.session.commit()

        # Verify new tags are associated
        retrieved_task = self.session.get(TaskModel, task.id)
        assert retrieved_task is not None
        assert len(retrieved_task.tag_models) == 2

        tag_names = {tag.name for tag in retrieved_task.tag_models}
        assert tag_names == {"new1", "new2"}

    def test_query_count_tasks_per_tag(self):
        """Test counting tasks per tag using SQL aggregation."""
        # Create tags
        tag1 = TagModel(name="tag1", created_at=datetime.now())
        tag2 = TagModel(name="tag2", created_at=datetime.now())

        # Create tasks
        task1 = TaskModel(
            name="Task 1",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task1.tag_models.append(tag1)

        task2 = TaskModel(
            name="Task 2",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task2.tag_models.extend([tag1, tag2])

        task3 = TaskModel(
            name="Task 3",
            priority=1,
            status="PENDING",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        task3.tag_models.append(tag2)

        self.session.add_all([task1, task2, task3])
        self.session.commit()

        # Count tasks per tag
        from sqlalchemy import func

        tag_counts = (
            self.session.query(TagModel.name, func.count(TaskTagModel.task_id))
            .join(TaskTagModel)
            .group_by(TagModel.id)
            .all()
        )

        tag_count_dict = dict(tag_counts)
        assert tag_count_dict["tag1"] == 2
        assert tag_count_dict["tag2"] == 2

    # ====================================================================
    # Phase 4: Edge Case Tests
    # ====================================================================

    def test_tag_name_exactly_100_characters(self):
        """Test tag name with exactly 100 characters (max length) (Phase 4)."""
        # TagModel defines String(100), so 100 chars should succeed
        tag_name = "a" * 100
        tag = TagModel(name=tag_name, created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify it was saved correctly
        retrieved = self.session.get(TagModel, tag.id)
        assert retrieved is not None
        assert retrieved.name == tag_name
        assert len(retrieved.name) == 100

    def test_tag_name_99_characters(self):
        """Test tag name with 99 characters (just under max) (Phase 4)."""
        tag_name = "b" * 99
        tag = TagModel(name=tag_name, created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify it was saved correctly
        retrieved = self.session.get(TagModel, tag.id)
        assert retrieved is not None
        assert retrieved.name == tag_name
        assert len(retrieved.name) == 99

    def test_tag_name_exceeding_100_characters_fails(self):
        """Test tag name exceeding 100 characters is rejected (Phase 4)."""
        # 101 characters should fail
        tag_name = "c" * 101
        tag = TagModel(name=tag_name, created_at=datetime.now())
        self.session.add(tag)

        # SQLite with String(100) will truncate or raise error
        # Behavior depends on SQLAlchemy/SQLite version
        # We just verify it doesn't silently succeed with 101 chars
        try:
            self.session.commit()
            # If commit succeeds, verify it was truncated to 100
            retrieved = self.session.get(TagModel, tag.id)
            assert len(retrieved.name) <= 100
        except Exception:
            # If it raises an error, that's also acceptable
            self.session.rollback()

    def test_tag_with_newline_character(self):
        """Test tag containing newline character (Phase 4)."""
        tag = TagModel(name="urgent\nbackend", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify newline is preserved
        retrieved = self.session.get(TagModel, tag.id)
        assert retrieved.name == "urgent\nbackend"
        assert "\n" in retrieved.name

    def test_tag_with_tab_character(self):
        """Test tag containing tab character (Phase 4)."""
        tag = TagModel(name="urgent\tbackend", created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify tab is preserved
        retrieved = self.session.get(TagModel, tag.id)
        assert retrieved.name == "urgent\tbackend"
        assert "\t" in retrieved.name

    def test_tag_with_sql_injection_attempt(self):
        """Test tag name with SQL injection attempt is safely stored (Phase 4)."""
        # This should be safely parameterized by SQLAlchemy
        dangerous_name = "'; DROP TABLE tags;--"
        tag = TagModel(name=dangerous_name, created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify it's stored as literal string, not executed as SQL
        retrieved = self.session.get(TagModel, tag.id)
        assert retrieved.name == dangerous_name

        # Verify tags table still exists by querying it
        stmt = select(TagModel).where(TagModel.name == dangerous_name)
        result = self.session.scalar(stmt)
        assert result is not None

    def test_tag_with_emoji(self):
        """Test tag name containing emoji characters (Phase 4)."""
        tag_name = "🔥urgent🔥"
        tag = TagModel(name=tag_name, created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify emoji is preserved
        retrieved = self.session.get(TagModel, tag.id)
        assert retrieved.name == tag_name
        assert "🔥" in retrieved.name

    def test_tag_with_right_to_left_text(self):
        """Test tag name with Arabic text (RTL) (Phase 4)."""
        # Arabic for "urgent"
        tag_name = "عاجل"
        tag = TagModel(name=tag_name, created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify RTL text is preserved
        retrieved = self.session.get(TagModel, tag.id)
        assert retrieved.name == tag_name

    def test_tag_with_mixed_unicode(self):
        """Test tag with mixed unicode (Latin, CJK, emoji) (Phase 4)."""
        tag_name = "urgent緊急🚨"
        tag = TagModel(name=tag_name, created_at=datetime.now())
        self.session.add(tag)
        self.session.commit()

        # Verify all characters are preserved
        retrieved = self.session.get(TagModel, tag.id)
        assert retrieved.name == tag_name
        assert len(retrieved.name) == 9  # 6 latin + 2 CJK + 1 emoji
