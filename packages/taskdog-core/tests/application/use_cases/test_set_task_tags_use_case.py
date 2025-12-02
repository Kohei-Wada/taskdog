"""Tests for SetTaskTagsUseCase."""

import pytest

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.dto.set_task_tags_input import SetTaskTagsInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.application.use_cases.set_task_tags import SetTaskTagsUseCase
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)


class TestSetTaskTagsUseCase:
    """Test cases for SetTaskTagsUseCase."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Initialize use case for each test."""
        self.repository = repository
        self.use_case = SetTaskTagsUseCase(self.repository)

        # Create a test task
        create_use_case = CreateTaskUseCase(self.repository)
        input_dto = CreateTaskInput(name="Test Task", priority=1)
        self.task = create_use_case.execute(input_dto)

    def test_execute_sets_tags_on_task(self):
        """Test execute sets tags on a task."""
        input_dto = SetTaskTagsInput(task_id=self.task.id, tags=["work", "urgent"])

        result = self.use_case.execute(input_dto)

        assert result.tags == ["work", "urgent"]
        assert result.id == self.task.id

    def test_execute_replaces_existing_tags(self):
        """Test execute replaces existing tags."""
        # Set initial tags
        input_dto1 = SetTaskTagsInput(task_id=self.task.id, tags=["work", "urgent"])
        self.use_case.execute(input_dto1)

        # Replace with new tags
        input_dto2 = SetTaskTagsInput(
            task_id=self.task.id, tags=["personal", "low-priority"]
        )
        result = self.use_case.execute(input_dto2)

        assert result.tags == ["personal", "low-priority"]

    def test_execute_clears_tags_with_empty_list(self):
        """Test execute clears tags when given empty list."""
        # Set initial tags
        input_dto1 = SetTaskTagsInput(task_id=self.task.id, tags=["work", "urgent"])
        self.use_case.execute(input_dto1)

        # Clear tags
        input_dto2 = SetTaskTagsInput(task_id=self.task.id, tags=[])
        result = self.use_case.execute(input_dto2)

        assert result.tags == []

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute raises error with nonexistent task ID."""
        input_dto = SetTaskTagsInput(task_id=9999, tags=["work"])

        with pytest.raises(TaskNotFoundException):
            self.use_case.execute(input_dto)

    def test_execute_with_empty_tag_raises_error(self):
        """Test execute raises error with empty tag."""
        input_dto = SetTaskTagsInput(task_id=self.task.id, tags=["work", "", "urgent"])

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert "Tag cannot be empty" in str(exc_info.value)

    def test_execute_with_duplicate_tags_raises_error(self):
        """Test execute raises error with duplicate tags."""
        input_dto = SetTaskTagsInput(
            task_id=self.task.id, tags=["work", "urgent", "work"]
        )

        with pytest.raises(TaskValidationError) as exc_info:
            self.use_case.execute(input_dto)

        assert "Tags must be unique" in str(exc_info.value)

    def test_execute_persists_tags_to_repository(self):
        """Test execute persists tags to repository."""
        input_dto = SetTaskTagsInput(task_id=self.task.id, tags=["work", "urgent"])
        self.use_case.execute(input_dto)

        # Reload task from repository
        reloaded_task = self.repository.get_by_id(self.task.id)

        assert reloaded_task.tags == ["work", "urgent"]

    def test_execute_with_special_characters_in_tags(self):
        """Test execute handles special characters in tags."""
        input_dto = SetTaskTagsInput(
            task_id=self.task.id, tags=["project-2024", "client_a", "v1.0"]
        )

        result = self.use_case.execute(input_dto)

        assert result.tags == ["project-2024", "client_a", "v1.0"]
