"""Tests for SqliteTaskRepository.delete_tag method."""

from pathlib import Path

import pytest

from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.domain.exceptions.tag_exceptions import TagNotFoundException
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestSqliteTaskRepositoryDeleteTag:
    """Test cases for SqliteTaskRepository.delete_tag."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures with temporary database."""
        self.temp_dir = tmp_path
        self.db_path = Path(self.temp_dir) / "test_tasks.db"
        self.database_url = f"sqlite:///{self.db_path}"
        self.mapper = TaskDbMapper()
        self.repository = SqliteTaskRepository(self.database_url, self.mapper)
        yield
        if hasattr(self.repository, "close"):
            self.repository.close()

    def _create_task_with_tags(self, name: str, tags: list[str]) -> Task:
        """Helper to create a task with tags."""
        return self.repository.create(
            name=name,
            priority=1,
            status=TaskStatus.PENDING,
            tags=tags,
        )

    def test_delete_tag_removes_tag(self):
        """Test delete_tag removes the tag record."""
        self._create_task_with_tags("Task 1", ["work", "urgent"])

        self.repository.delete_tag("urgent")

        tag_counts = self.repository.get_tag_counts()
        assert "urgent" not in tag_counts

    def test_delete_tag_returns_affected_count(self):
        """Test delete_tag returns correct affected task count."""
        self._create_task_with_tags("Task 1", ["work", "urgent"])
        self._create_task_with_tags("Task 2", ["work", "personal"])

        affected = self.repository.delete_tag("work")

        assert affected == 2

    def test_delete_tag_with_single_task(self):
        """Test delete_tag with tag on single task."""
        self._create_task_with_tags("Task 1", ["unique-tag"])

        affected = self.repository.delete_tag("unique-tag")

        assert affected == 1

    def test_delete_tag_with_no_tasks(self):
        """Test delete_tag with tag that has zero task associations."""
        # Create tag via task, then remove from task but tag persists
        task = self._create_task_with_tags("Task 1", ["orphan-tag", "other"])
        # Remove orphan-tag from task by setting only "other"
        task.tags = ["other"]
        self.repository.save(task)

        affected = self.repository.delete_tag("orphan-tag")

        assert affected == 0

    def test_delete_tag_preserves_other_tags(self):
        """Test delete_tag does not affect other tags."""
        task = self._create_task_with_tags("Task 1", ["work", "urgent"])

        self.repository.delete_tag("urgent")

        reloaded = self.repository.get_by_id(task.id)
        assert "work" in reloaded.tags
        assert "urgent" not in reloaded.tags

    def test_delete_tag_nonexistent_raises_error(self):
        """Test delete_tag raises TagNotFoundException for nonexistent tag."""
        with pytest.raises(TagNotFoundException) as exc_info:
            self.repository.delete_tag("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_delete_tag_cascade_removes_associations(self):
        """Test that CASCADE delete removes task_tags associations."""
        task1 = self._create_task_with_tags("Task 1", ["shared", "a"])
        task2 = self._create_task_with_tags("Task 2", ["shared", "b"])

        self.repository.delete_tag("shared")

        # Both tasks should no longer have the deleted tag
        t1 = self.repository.get_by_id(task1.id)
        t2 = self.repository.get_by_id(task2.id)
        assert "shared" not in t1.tags
        assert "shared" not in t2.tags
        # Other tags should remain
        assert "a" in t1.tags
        assert "b" in t2.tags
