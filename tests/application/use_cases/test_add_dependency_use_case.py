"""Tests for AddDependencyUseCase."""

import os
import tempfile
import unittest

from application.dto.manage_dependencies_input import AddDependencyInput
from application.use_cases.add_dependency import AddDependencyUseCase
from domain.exceptions.task_exceptions import TaskNotFoundException, TaskValidationError
from infrastructure.persistence.json_task_repository import JsonTaskRepository


class TestAddDependencyUseCase(unittest.TestCase):
    """Test cases for AddDependencyUseCase."""

    def setUp(self):
        """Create temporary file and initialize use case for each test."""
        self.test_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        self.test_file.close()
        self.test_filename = self.test_file.name
        self.repository = JsonTaskRepository(self.test_filename)
        self.use_case = AddDependencyUseCase(self.repository)

    def tearDown(self):
        """Clean up temporary file after each test."""
        if os.path.exists(self.test_filename):
            os.unlink(self.test_filename)

    def test_execute_adds_dependency(self):
        """Test execute adds dependency to task."""
        # Create two tasks
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        input_dto = AddDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        result = self.use_case.execute(input_dto)

        self.assertIn(task1.id, result.depends_on)
        self.assertEqual(len(result.depends_on), 1)

    def test_execute_persists_changes(self):
        """Test execute saves dependency to repository."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        input_dto = AddDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto)

        # Verify persistence
        retrieved = self.repository.get_by_id(task2.id)
        self.assertIn(task1.id, retrieved.depends_on)

    def test_execute_with_nonexistent_task_raises_error(self):
        """Test execute with non-existent task raises TaskNotFoundException."""
        task1 = self.repository.create(name="Task 1", priority=1)

        input_dto = AddDependencyInput(task_id=999, depends_on_id=task1.id)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_with_nonexistent_dependency_raises_error(self):
        """Test execute with non-existent dependency raises TaskNotFoundException."""
        task1 = self.repository.create(name="Task 1", priority=1)

        input_dto = AddDependencyInput(task_id=task1.id, depends_on_id=999)

        with self.assertRaises(TaskNotFoundException) as context:
            self.use_case.execute(input_dto)

        self.assertEqual(context.exception.task_id, 999)

    def test_execute_prevents_self_dependency(self):
        """Test execute prevents task from depending on itself."""
        task1 = self.repository.create(name="Task 1", priority=1)

        input_dto = AddDependencyInput(task_id=task1.id, depends_on_id=task1.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("cannot depend on itself", str(context.exception))

    def test_execute_prevents_duplicate_dependency(self):
        """Test execute prevents adding same dependency twice."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        # Add dependency first time
        input_dto = AddDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto)

        # Try to add again
        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto)

        self.assertIn("already depends on", str(context.exception))

    def test_execute_detects_circular_dependency(self):
        """Test execute detects simple circular dependency."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)

        # task2 depends on task1
        input_dto1 = AddDependencyInput(task_id=task2.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto1)

        # Try to make task1 depend on task2 (circular)
        input_dto2 = AddDependencyInput(task_id=task1.id, depends_on_id=task2.id)

        with self.assertRaises(TaskValidationError) as context:
            self.use_case.execute(input_dto2)

        self.assertIn("Circular dependency", str(context.exception))

    def test_execute_allows_multiple_dependencies(self):
        """Test execute allows task to have multiple dependencies."""
        task1 = self.repository.create(name="Task 1", priority=1)
        task2 = self.repository.create(name="Task 2", priority=1)
        task3 = self.repository.create(name="Task 3", priority=1)

        # task3 depends on both task1 and task2
        input_dto1 = AddDependencyInput(task_id=task3.id, depends_on_id=task1.id)
        self.use_case.execute(input_dto1)

        input_dto2 = AddDependencyInput(task_id=task3.id, depends_on_id=task2.id)
        result = self.use_case.execute(input_dto2)

        self.assertIn(task1.id, result.depends_on)
        self.assertIn(task2.id, result.depends_on)
        self.assertEqual(len(result.depends_on), 2)


if __name__ == "__main__":
    unittest.main()
