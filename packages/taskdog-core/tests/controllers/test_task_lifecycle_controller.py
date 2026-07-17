"""Tests for TaskLifecycleController."""

from datetime import datetime
from unittest.mock import MagicMock, Mock

import pytest

from taskdog_core.controllers.task_lifecycle_controller import TaskLifecycleController
from taskdog_core.domain.entities.task import Task, TaskStatus
from taskdog_core.infrastructure.persistence.database.sqlite_task_repository import (
    SqliteTaskRepository,
)


class TestTaskLifecycleController:
    """Test cases for TaskLifecycleController."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.repository = Mock(spec=SqliteTaskRepository)
        self.config = MagicMock()
        self.controller = TaskLifecycleController(
            repository=self.repository,
            config=self.config,
        )

    @pytest.mark.parametrize(
        "operation,initial_status,actual_start,actual_end",
        [
            (
                "start",
                TaskStatus.PENDING,
                None,
                None,
            ),
            (
                "complete",
                TaskStatus.IN_PROGRESS,
                datetime(2025, 1, 1, 9, 0, 0),
                None,
            ),
            (
                "pause",
                TaskStatus.IN_PROGRESS,
                datetime(2025, 1, 1, 9, 0, 0),
                None,
            ),
            (
                "cancel",
                TaskStatus.IN_PROGRESS,
                datetime(2025, 1, 1, 9, 0, 0),
                None,
            ),
            (
                "reopen",
                TaskStatus.COMPLETED,
                datetime(2025, 1, 1, 9, 0, 0),
                datetime(2025, 1, 1, 17, 0, 0),
            ),
        ],
    )
    def test_lifecycle_operation_returns_status_change_output(
        self, operation, initial_status, actual_start, actual_end
    ):
        """Test that lifecycle operations return StatusChangeOutput."""
        # Arrange
        task_id = 1
        task = Task(
            id=task_id,
            name="Test Task",
            priority=1,
            status=initial_status,
            actual_start=actual_start,
            actual_end=actual_end,
        )
        self.repository.get_by_id.return_value = task
        self.repository.save.return_value = None

        # Act
        result = self.controller.execute_lifecycle(operation, task_id)

        # Assert
        assert result is not None
        assert result.task.id == task_id
        assert result.task.name == "Test Task"
        assert result.old_status == initial_status

    def test_invalid_operation_raises_value_error(self):
        """Test that an unknown lifecycle operation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid lifecycle operation"):
            self.controller.execute_lifecycle("bogus", 1)

    def test_controller_inherits_from_base_controller(self):
        """Test that controller has repository and config from base class."""
        assert self.controller.repository is not None
        assert self.controller.config is not None
        assert self.controller.repository == self.repository
        assert self.controller.config == self.config
