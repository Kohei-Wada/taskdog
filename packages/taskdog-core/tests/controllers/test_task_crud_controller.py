"""Tests for TaskCrudController."""

import unittest
from unittest.mock import MagicMock

from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.domain.entities.task import Task, TaskStatus
from tests.test_fixtures import InMemoryDatabaseTestCase


class TestTaskCrudController(InMemoryDatabaseTestCase):
    """Test cases for TaskCrudController."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.notes_repository = MagicMock()
        self.config = MagicMock()
        self.config.task.default_priority = 3
        self.controller = TaskCrudController(
            repository=self.repository,
            notes_repository=self.notes_repository,
            config=self.config,
        )

    def test_create_task_returns_task_operation_output(self):
        """Test that create_task returns TaskOperationOutput."""
        # Act
        result = self.controller.create_task(name="Test Task")

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Test Task")
        self.assertIsNotNone(result.id)

        # Verify task was persisted
        persisted_task = self.repository.get_by_id(result.id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.name, "Test Task")

    def test_create_task_uses_config_default_priority(self):
        """Test that create_task uses config default priority when not specified."""
        # Act
        result = self.controller.create_task(name="Test Task")

        # Assert
        self.assertEqual(result.priority, 3)  # From config

    def test_update_task_returns_update_task_output(self):
        """Test that update_task returns TaskUpdateOutput."""
        # Create a task
        task = Task(name="Original Name", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Act
        result = self.controller.update_task(task_id=task.id, name="New Name")

        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.task)
        self.assertIsNotNone(result.updated_fields)
        self.assertEqual(result.task.name, "New Name")

        # Verify task was persisted
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertEqual(persisted_task.name, "New Name")

    def test_archive_task_returns_task_operation_output(self):
        """Test that archive_task returns TaskOperationOutput."""
        # Create a task
        task = Task(
            name="Test Task", priority=1, status=TaskStatus.PENDING, is_archived=False
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Act
        result = self.controller.archive_task(task.id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task.id)

        # Verify task was archived
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertTrue(persisted_task.is_archived)

    def test_restore_task_returns_task_operation_output(self):
        """Test that restore_task returns TaskOperationOutput."""
        # Create an archived task
        task = Task(
            name="Test Task", priority=1, status=TaskStatus.PENDING, is_archived=True
        )
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Act
        result = self.controller.restore_task(task.id)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result.id, task.id)

        # Verify task was restored
        persisted_task = self.repository.get_by_id(task.id)
        self.assertIsNotNone(persisted_task)
        self.assertFalse(persisted_task.is_archived)

    def test_remove_task_calls_repository(self):
        """Test that remove_task calls repository delete method."""
        # Create a task
        task = Task(name="Test Task", priority=1, status=TaskStatus.PENDING)
        task.id = self.repository.generate_next_id()
        self.repository.save(task)

        # Act
        self.controller.remove_task(task.id)

        # Assert - task should no longer exist
        deleted_task = self.repository.get_by_id(task.id)
        self.assertIsNone(deleted_task)

        # Assert - notes deletion should be called
        self.notes_repository.delete_notes.assert_called_once_with(task.id)

    def test_controller_inherits_from_base_controller(self):
        """Test that controller has repository and config from base class."""
        self.assertIsNotNone(self.controller.repository)
        self.assertIsNotNone(self.controller.config)
        self.assertEqual(self.controller.repository, self.repository)
        self.assertEqual(self.controller.config, self.config)


if __name__ == "__main__":
    unittest.main()
