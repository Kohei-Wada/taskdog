"""Tests for TaskRelationshipController."""

from unittest.mock import MagicMock, Mock

import pytest

from taskdog_core.controllers.task_relationship_controller import (
    TaskRelationshipController,
)
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestTaskRelationshipController:
    """Test cases for TaskRelationshipController."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=SqliteTaskRepository)
        self.config = MagicMock()
        self.controller = TaskRelationshipController(
            repository=self.repository,
            config=self.config,
        )

    def test_add_dependency_returns_task_operation_output(self):
        """Test that add_dependency returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        depends_on_id = 2
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            depends_on=[],
        )
        dependency_task = Task(
            id=depends_on_id,
            name="Dependency Task",
            priority=1,
            status=TaskStatus.PENDING,
        )

        tasks_by_id = {task_id: task, depends_on_id: dependency_task}
        self.repository.get_by_id.side_effect = tasks_by_id.get
        self.repository.get_by_ids.side_effect = lambda ids: {
            tid: tasks_by_id[tid] for tid in ids if tid in tasks_by_id
        }
        self.repository.save.return_value = None

        # Act
        result = self.controller.add_dependency(task_id, depends_on_id)

        # Assert
        assert result is not None
        assert result.id == task_id

    def test_remove_dependency_returns_task_operation_output(self):
        """Test that remove_dependency returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        depends_on_id = 2
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            depends_on=[depends_on_id],
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.remove_dependency(task_id, depends_on_id)

        # Assert
        assert result is not None
        assert result.id == task_id

    def test_set_task_tags_returns_task_operation_output(self):
        """Test that set_task_tags returns TaskOperationOutput."""
        # Arrange
        task_id = 1
        tags = ["work", "urgent"]
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=TaskStatus.PENDING,
            tags=[],
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.set_task_tags(task_id, tags)

        # Assert
        assert result is not None
        assert result.id == task_id

    def test_controller_inherits_from_base_controller(self):
        """Test that controller has repository and config from base class."""
        assert self.controller.repository is not None
        assert self.controller.config is not None
        assert self.controller.repository == self.repository
        assert self.controller.config == self.config
