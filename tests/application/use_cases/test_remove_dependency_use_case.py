"""Tests for RemoveDependencyUseCase."""

import os
import tempfile
import unittest

from application.dto.manage_dependencies_input import RemoveDependencyInput
from application.use_cases.remove_dependency import RemoveDependencyUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestRemoveDependencyUseCase(unittest.TestCase):
    """Test cases for RemoveDependencyUseCase."""

    def setUp(self):
        """Create temporary file and initialize use case for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.use_case = RemoveDependencyUseCase(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_removes_dependency(self):
        """Test execute removes dependency from task."""
        # Create two tasks with dependency
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1, depends_on=[task1.id])

        input_dto = RemoveDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        result = self.use_case.execute(input_dto)

        self.assertNotIn(task1.id, result.depends_on)
        self.assertEqual(len(result.depends_on), 0)

    def test_execute_persists_changes(self):
        """Test execute saves changes to repository."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1, depends_on=[task1.id])

        input_dto = RemoveDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task2.id)
        self.assertNotIn(task1.id, retrieved.depends_on)
        self.assertEqual(len(retrieved.depends_on), 0)

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        input_dto = RemoveDependencyInput(task_id=999, depends_on_id=1)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_with_nonexistent_dependency_raises_error(self):
        """Test execute with non-existent dependency raises TaskValidationError."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        input_dto = RemoveDependencyInput(task_id=task2.id, depends_on_id=task1.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("does not depend on", str(context.exception))

    def test_execute_preserves_other_dependencies(self):
        """Test execute only removes specified dependency."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1, depends_on=[task1.id, task2.id])

        # Remove only task1 dependency
        input_dto = RemoveDependencyInput(task_id=task3.id, depends_on_id=task1.id)
        result = self.use_case.execute(input_dto)

        self.assertNotIn(task1.id, result.depends_on)
        self.assertIn(task2.id, result.depends_on)
        self.assertEqual(len(result.depends_on), 1)

    def test_execute_with_empty_dependencies_raises_error(self):
        """Test execute with task that has no dependencies raises error."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        input_dto = RemoveDependencyInput(task_id=task2.id, depends_on_id=task1.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("does not depend on", str(context.exception))


if __name__ == "__main__":
    unittest.main()
