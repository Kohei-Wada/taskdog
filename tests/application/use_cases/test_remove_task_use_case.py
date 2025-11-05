"""Tests for RemoveTaskUseCase."""

import tempfile
import unittest

from application.dto.remove_task_input import RemoveTaskInput
from application.use_cases.remove_task import RemoveTaskUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException
from infrastructure.persistence.database.sqlite_task_repository import SqliteTaskRepository


class RemoveTaskUseCaseTest(unittest.TestCase):
    """Test cases for RemoveTaskUseCase."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db")
        self.temp_file.close()

        self.repository = SqliteTaskRepository(f"sqlite:///{self.temp_file.name}")
        self.use_case = RemoveTaskUseCase(self.repository)

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, "repository") and hasattr(self.repository, "close"):
            self.repository.close()
        import os

        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_remove_task(self):
        """Test removing a task."""
        # Create task
        task = self.repository.create(name="Test Task", priority=1)

        # Remove task
        input_dto = RemoveTaskInput(task_id=task.id)
        self.use_case.execute(input_dto)

        # Verify task removed
        self.assertIsNone(self.repository.get_by_id(task.id))

    def test_remove_nonexistent_task(self):
        """Test removing a task that doesn't exist."""
        input_dto = RemoveTaskInput(task_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)


if __name__ == "__main__":
    unittest.main()
