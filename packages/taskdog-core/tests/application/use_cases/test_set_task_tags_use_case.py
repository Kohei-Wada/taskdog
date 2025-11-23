import unittest
"""Tests for SetTaskTagsUseCase."""

from taskdog_core.application.dto.create_task_input import CreateTaskInput
from taskdog_core.application.dto.set_task_tags_input import SetTaskTagsInput
from taskdog_core.application.use_cases.create_task import CreateTaskUseCase
from taskdog_core.application.use_cases.set_task_tags import SetTaskTagsUseCase
from taskdog_core.domain.exceptions.task_exceptions import (
    TaskNotFoundException,
    TaskValidationError,
)
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestSetTaskTagsUseCase(InMemoryDatabaseTestCase):
    """Test cases for SetTaskTagsUseCase."""

    def setUp(self):
        """Initialize use case for each test."""
        super().setUp()
        self.use_case = SetTaskTagsUseCase(self.repository)

        # Create a test task
        create_use_case = CreateTaskUseCase(self.repository)
        input_dto = CreateTaskInput(name="Test Task", priority=1)
        self.task = create_use_case.execute(input_dto)

    def test_execute_sets_tags_on_task(self):
        """Test execute sets tags on a task."""
        input_dto = SetTaskTagsInput(task_id=self.task.id, tags=["work", "urgent"])

        result = self.use_case.execute(input_dto)

        self.assertEqual(result.tags, ["work", "urgent"])
        self.assertEqual(result.id, self.task.id)

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

        self.assertEqual(result.tags, ["personal", "low-priority"])

    def test_execute_clears_tags_with_empty_list(self):
        """Test execute clears tags when given empty list."""
        # Set initial tags
        input_dto1 = SetTaskTagsInput(task_id=self.task.id, tags=["work", "urgent"])
        self.use_case.execute(input_dto1)

        # Clear tags
        input_dto2 = SetTaskTagsInput(task_id=self.task.id, tags=[])
        result = self.use_case.execute(input_dto2)

        self.assertEqual(result.tags, [])

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute raises error with nonexistent task ID."""
        input_dto = SetTaskTagsInput(task_id=9999, tags=["work"])

        with self.assertRaises(TaskNotFoundException):
            self.use_case.execute(input_dto)

    def test_execute_with_empty_tag_raises_error(self):
        """Test execute raises error with empty tag."""
        input_dto = SetTaskTagsInput(task_id=self.task.id, tags=["work", "", "urgent"])

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Tag cannot be empty", str(context.exception))

    def test_execute_with_duplicate_tags_raises_error(self):
        """Test execute raises error with duplicate tags."""
        input_dto = SetTaskTagsInput(
            task_id=self.task.id, tags=["work", "urgent", "work"]
        )

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("Tags must be unique", str(context.exception))

    def test_execute_persists_tags_to_repository(self):
        """Test execute persists tags to repository."""
        input_dto = SetTaskTagsInput(task_id=self.task.id, tags=["work", "urgent"])
        self.use_case.execute(input_dto)

        # Reload task from repository
        reloaded_task = self.repository.get_by_id(self.task.id)

        self.assertEqual(reloaded_task.tags, ["work", "urgent"])

    def test_execute_with_special_characters_in_tags(self):
        """Test execute handles special characters in tags."""
        input_dto = SetTaskTagsInput(
            task_id=self.task.id, tags=["project-2024", "client_a", "v1.0"]
        )

        result = self.use_case.execute(input_dto)

        self.assertEqual(result.tags, ["project-2024", "client_a", "v1.0"])


if __name__ == "__main__":
    unittest.main()
