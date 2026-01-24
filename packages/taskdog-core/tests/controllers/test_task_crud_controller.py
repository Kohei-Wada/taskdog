"""Tests for TaskCrudController."""

from unittest.mock import MagicMock, Mock

import pytest

from taskdog_core.controllers.task_crud_controller import TaskCrudController
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_core.domain.services.logger import Logger


class TestTaskCrudController:
    """Test cases for TaskCrudController."""

    @pytest.fixture(autouse=True)
    def setup(self, repository):
        """Set up test fixtures."""
        self.repository = repository
        self.notes_repository = MagicMock()
        self.config = MagicMock()
        self.logger = Mock(spec=Logger)
        self.controller = TaskCrudController(
            repository=self.repository,
            notes_repository=self.notes_repository,
            config=self.config,
            logger=self.logger,
        )

    def test_create_task_returns_task_operation_output(self):
        """Test that create_task returns TaskOperationOutput."""
        # Act
        result = self.controller.create_task(name="Test Task")

        # Assert
        assert result is not None
        assert result.name == "Test Task"
        assert result.id is not None

        # Verify task was persisted
        persisted_task = self.repository.get_by_id(result.id)
        assert persisted_task is not None
        assert persisted_task.name == "Test Task"

    def test_create_task_without_priority_sets_none(self):
        """Test that create_task leaves priority as None when not specified."""
        # Act
        result = self.controller.create_task(name="Test Task")

        # Assert
        assert result.priority is None  # No default priority

    def test_update_task_returns_update_task_output(self):
        """Test that update_task returns TaskUpdateOutput."""
        # Create a task
        task = self.repository.create(
            name="Original Name", priority=1, status=TaskStatus.PENDING
        )

        # Act
        result = self.controller.update_task(task_id=task.id, name="New Name")

        # Assert
        assert result is not None
        assert result.task is not None
        assert result.updated_fields is not None
        assert result.task.name == "New Name"

        # Verify task was persisted
        persisted_task = self.repository.get_by_id(task.id)
        assert persisted_task is not None
        assert persisted_task.name == "New Name"

    def test_archive_task_returns_task_operation_output(self):
        """Test that archive_task returns TaskOperationOutput."""
        # Create a task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING, is_archived=False
        )

        # Act
        result = self.controller.archive_task(task.id)

        # Assert
        assert result is not None
        assert result.id == task.id

        # Verify task was archived
        persisted_task = self.repository.get_by_id(task.id)
        assert persisted_task is not None
        assert persisted_task.is_archived is True

    def test_restore_task_returns_task_operation_output(self):
        """Test that restore_task returns TaskOperationOutput."""
        # Create an archived task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING, is_archived=True
        )

        # Act
        result = self.controller.restore_task(task.id)

        # Assert
        assert result is not None
        assert result.id == task.id

        # Verify task was restored
        persisted_task = self.repository.get_by_id(task.id)
        assert persisted_task is not None
        assert persisted_task.is_archived is False

    def test_remove_task_calls_repository(self):
        """Test that remove_task calls repository delete method."""
        # Create a task
        task = self.repository.create(
            name="Test Task", priority=1, status=TaskStatus.PENDING
        )

        # Act
        self.controller.remove_task(task.id)

        # Assert - task should no longer exist
        deleted_task = self.repository.get_by_id(task.id)
        assert deleted_task is None

        # Assert - notes deletion should be called
        self.notes_repository.delete_notes.assert_called_once_with(task.id)

    def test_controller_inherits_from_base_controller(self):
        """Test that controller has repository and config from base class."""
        assert self.controller.repository is not None
        assert self.controller.config is not None
        assert self.controller.repository == self.repository
        assert self.controller.config == self.config
