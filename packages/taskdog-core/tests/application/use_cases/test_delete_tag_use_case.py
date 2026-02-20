"""Tests for DeleteTagUseCase."""

from pathlib import Path

import pytest

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.dto.delete_tag_input import DeleteTagInput
from taskdog_core.application.dto.set_task_tags_input import SetTaskTagsInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.application.use_cases.delete_tag import DeleteTagUseCase
from taskdog_core.application.use_cases.set_task_tags import SetTaskTagsUseCase
from taskdog_core.domain.exceptions.tag_exceptions import TagNotFoundException
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)
from taskdog_core.infrastructure.persistence.mappers.task_db_mapper import TaskDbMapper


class TestDeleteTagUseCase:
    """Test cases for DeleteTagUseCase.

    Uses its own isolated repository to avoid corrupting the shared
    session-scoped tags table (delete_tag removes tag records).
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Initialize use case with isolated repository for each test."""
        db_path = Path(tmp_path) / "test_delete_tag.db"
        database_url = f"sqlite:///{db_path}"
        self.repository = SqliteTaskRepository(database_url, TaskDbMapper())
        self.use_case = DeleteTagUseCase(self.repository)
        self.set_tags_use_case = SetTaskTagsUseCase(self.repository)

        # Create test tasks with tags
        create_use_case = CreateTaskUseCase(self.repository)
        self.task1 = create_use_case.execute(CreateTaskInput(name="Task 1", priority=1))
        self.task2 = create_use_case.execute(CreateTaskInput(name="Task 2", priority=1))

        # Set tags on tasks
        self.set_tags_use_case.execute(
            SetTaskTagsInput(task_id=self.task1.id, tags=["work", "urgent"])
        )
        self.set_tags_use_case.execute(
            SetTaskTagsInput(task_id=self.task2.id, tags=["work", "personal"])
        )
        yield
        if hasattr(self.repository, "close"):
            self.repository.close()

    def test_execute_deletes_tag(self):
        """Test execute deletes a tag and returns correct output."""
        input_dto = DeleteTagInput(tag_name="urgent")

        result = self.use_case.execute(input_dto)

        assert result.tag_name == "urgent"
        assert result.affected_task_count == 1

    def test_execute_deletes_shared_tag(self):
        """Test deleting a tag shared by multiple tasks."""
        input_dto = DeleteTagInput(tag_name="work")

        result = self.use_case.execute(input_dto)

        assert result.tag_name == "work"
        assert result.affected_task_count == 2

    def test_execute_removes_tag_from_tasks(self):
        """Test that deleting a tag removes it from associated tasks."""
        self.use_case.execute(DeleteTagInput(tag_name="work"))

        # Reload tasks and verify tag is removed
        task1 = self.repository.get_by_id(self.task1.id)
        task2 = self.repository.get_by_id(self.task2.id)

        assert "work" not in task1.tags
        assert "work" not in task2.tags

    def test_execute_preserves_other_tags(self):
        """Test that deleting a tag preserves other tags on tasks."""
        self.use_case.execute(DeleteTagInput(tag_name="work"))

        task1 = self.repository.get_by_id(self.task1.id)
        task2 = self.repository.get_by_id(self.task2.id)

        assert "urgent" in task1.tags
        assert "personal" in task2.tags

    def test_execute_with_nonexistent_tag_raises_error(self):
        """Test execute raises TagNotFoundException for nonexistent tag."""
        input_dto = DeleteTagInput(tag_name="nonexistent")

        with pytest.raises(TagNotFoundException) as exc_info:
            self.use_case.execute(input_dto)

        assert "nonexistent" in str(exc_info.value)

    def test_execute_deletes_tag_with_zero_tasks(self):
        """Test deleting a tag that exists but has no tasks after removal."""
        # Create a unique tag on task1
        self.set_tags_use_case.execute(
            SetTaskTagsInput(task_id=self.task1.id, tags=["unique-tag"])
        )

        # Delete the unique tag
        result = self.use_case.execute(DeleteTagInput(tag_name="unique-tag"))

        assert result.tag_name == "unique-tag"
        assert result.affected_task_count == 1
