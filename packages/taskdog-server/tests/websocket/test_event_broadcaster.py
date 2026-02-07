"""Tests for WebSocketEventBroadcaster."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_server.websocket.broadcaster import WebSocketEventBroadcaster
from taskdog_server.websocket.connection_manager import ConnectionManager


class TestWebSocketEventBroadcaster:
    """Test cases for WebSocketEventBroadcaster."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_manager = MagicMock(spec=ConnectionManager)
        self.mock_manager.broadcast = AsyncMock()
        self.mock_background_tasks = MagicMock()
        self.broadcaster = WebSocketEventBroadcaster(
            self.mock_manager, self.mock_background_tasks
        )

    def _create_task_output(
        self,
        task_id: int = 1,
        name: str = "Test Task",
        status: TaskStatus = TaskStatus.PENDING,
        priority: int = 1,
    ) -> TaskOperationOutput:
        """Create a TaskOperationOutput for testing."""
        return TaskOperationOutput(
            id=task_id,
            name=name,
            status=status,
            priority=priority,
            deadline=None,
            estimated_duration=None,
            planned_start=None,
            planned_end=None,
            actual_start=None,
            actual_end=None,
            actual_duration=None,
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            daily_allocations={},
        )

    def test_task_created_schedules_broadcast(self):
        """Test task_created schedules background task."""
        # Arrange
        task = self._create_task_output()
        source_user_name = "test-client"

        # Act
        self.broadcaster.task_created(task, source_user_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][0] == self.broadcaster._broadcast
        assert call_args[0][1] == "task_created"
        assert call_args[0][2] == {
            "task_id": 1,
            "task_name": "Test Task",
            "priority": 1,
            "status": "PENDING",
        }
        assert call_args[0][3] == "test-client"

    def test_task_created_without_source_user(self):
        """Test task_created with no source user."""
        # Arrange
        task = self._create_task_output()

        # Act
        self.broadcaster.task_created(task)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][3] is None

    def test_task_updated_schedules_broadcast(self):
        """Test task_updated schedules background task."""
        # Arrange
        task = self._create_task_output()
        fields = ["name", "priority"]
        source_user_name = "test-client-2"

        # Act
        self.broadcaster.task_updated(task, fields, source_user_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][0] == self.broadcaster._broadcast
        assert call_args[0][1] == "task_updated"
        assert call_args[0][2] == {
            "task_id": 1,
            "task_name": "Test Task",
            "updated_fields": ["name", "priority"],
            "status": "PENDING",
        }
        assert call_args[0][3] == "test-client-2"

    def test_task_updated_with_single_field(self):
        """Test task_updated with a single field."""
        # Arrange
        task = self._create_task_output()
        fields = ["is_archived"]

        # Act
        self.broadcaster.task_updated(task, fields)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][2]["updated_fields"] == ["is_archived"]

    def test_task_deleted_schedules_broadcast(self):
        """Test task_deleted schedules background task."""
        # Arrange
        task_id = 123
        task_name = "Deleted Task"
        source_user_name = "test-client-3"

        # Act
        self.broadcaster.task_deleted(task_id, task_name, source_user_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][0] == self.broadcaster._broadcast
        assert call_args[0][1] == "task_deleted"
        assert call_args[0][2] == {
            "task_id": 123,
            "task_name": "Deleted Task",
        }
        assert call_args[0][3] == "test-client-3"

    def test_task_deleted_without_source_user(self):
        """Test task_deleted with no source user."""
        # Arrange
        task_id = 456
        task_name = "Another Task"

        # Act
        self.broadcaster.task_deleted(task_id, task_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][3] is None

    def test_task_status_changed_schedules_broadcast(self):
        """Test task_status_changed schedules background task."""
        # Arrange
        task = self._create_task_output(status=TaskStatus.IN_PROGRESS)
        old_status = "PENDING"
        source_user_name = "test-client-4"

        # Act
        self.broadcaster.task_status_changed(task, old_status, source_user_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][0] == self.broadcaster._broadcast
        assert call_args[0][1] == "task_status_changed"
        assert call_args[0][2] == {
            "task_id": 1,
            "task_name": "Test Task",
            "old_status": "PENDING",
            "new_status": "IN_PROGRESS",
        }
        assert call_args[0][3] == "test-client-4"

    def test_task_status_changed_with_different_statuses(self):
        """Test task_status_changed with various status transitions."""
        # Arrange
        task = self._create_task_output(status=TaskStatus.COMPLETED)
        old_status = "IN_PROGRESS"

        # Act
        self.broadcaster.task_status_changed(task, old_status)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][2]["old_status"] == "IN_PROGRESS"
        assert call_args[0][2]["new_status"] == "COMPLETED"

    def test_task_notes_updated_schedules_broadcast(self):
        """Test task_notes_updated schedules background task."""
        # Arrange
        task_id = 789
        task_name = "Task with Notes"
        source_user_name = "test-client-5"

        # Act
        self.broadcaster.task_notes_updated(task_id, task_name, source_user_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][0] == self.broadcaster._broadcast
        assert call_args[0][1] == "task_updated"
        assert call_args[0][2] == {
            "task_id": 789,
            "task_name": "Task with Notes",
            "updated_fields": ["notes"],
        }
        assert call_args[0][3] == "test-client-5"

    def test_task_notes_updated_without_source_user(self):
        """Test task_notes_updated with no source user."""
        # Arrange
        task_id = 101
        task_name = "Notes Task"

        # Act
        self.broadcaster.task_notes_updated(task_id, task_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][3] is None

    def test_schedule_optimized_schedules_broadcast(self):
        """Test schedule_optimized schedules background task."""
        # Arrange
        scheduled_count = 5
        failed_count = 2
        algorithm = "greedy"
        source_user_name = "test-client-6"

        # Act
        self.broadcaster.schedule_optimized(
            scheduled_count, failed_count, algorithm, source_user_name
        )

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        assert call_args[0][0] == self.broadcaster._broadcast
        assert call_args[0][1] == "schedule_optimized"
        assert call_args[0][2] == {
            "scheduled_count": 5,
            "failed_count": 2,
            "algorithm": "greedy",
        }
        assert call_args[0][3] == "test-client-6"

    def test_schedule_optimized_with_different_algorithms(self):
        """Test schedule_optimized with various algorithms."""
        algorithms = ["greedy", "balanced", "backward", "priority_first", "genetic"]

        for algorithm in algorithms:
            # Reset mock for each iteration
            self.mock_background_tasks.reset_mock()

            # Act
            self.broadcaster.schedule_optimized(10, 0, algorithm)

            # Assert
            self.mock_background_tasks.add_task.assert_called_once()
            call_args = self.mock_background_tasks.add_task.call_args
            assert call_args[0][2]["algorithm"] == algorithm

    def test_multiple_broadcasts_in_sequence(self):
        """Test multiple broadcast calls are scheduled correctly."""
        # Arrange
        task1 = self._create_task_output(task_id=1, name="Task 1")
        task2 = self._create_task_output(task_id=2, name="Task 2")

        # Act
        self.broadcaster.task_created(task1, "client-1")
        self.broadcaster.task_updated(task2, ["priority"], "client-2")
        self.broadcaster.task_deleted(3, "Task 3", "client-3")

        # Assert
        assert self.mock_background_tasks.add_task.call_count == 3

    def test_broadcaster_stores_manager_and_background_tasks(self):
        """Test that broadcaster stores manager and background_tasks internally."""
        # Assert
        assert self.broadcaster._manager == self.mock_manager
        assert self.broadcaster._background_tasks == self.mock_background_tasks


class TestWebSocketEventBroadcasterBroadcast:
    """Async test cases for WebSocketEventBroadcaster._broadcast method."""

    async def test_broadcast_adds_type_and_source_user_name(self):
        """Test _broadcast adds type and source_user_name to payload."""
        # Arrange
        mock_manager = MagicMock(spec=ConnectionManager)
        mock_manager.broadcast = AsyncMock()
        mock_background_tasks = MagicMock()
        broadcaster = WebSocketEventBroadcaster(mock_manager, mock_background_tasks)

        payload = {"task_id": 1, "task_name": "Test"}
        source_user_name = "test-client"

        # Act
        await broadcaster._broadcast("task_created", payload, source_user_name)

        # Assert
        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        broadcast_payload = call_args[0][0]
        assert broadcast_payload["type"] == "task_created"
        assert broadcast_payload["source_user_name"] == "test-client"
        assert broadcast_payload["task_id"] == 1
        assert broadcast_payload["task_name"] == "Test"

    async def test_broadcast_with_none_source_user_name(self):
        """Test _broadcast with None source_user_name."""
        # Arrange
        mock_manager = MagicMock(spec=ConnectionManager)
        mock_manager.broadcast = AsyncMock()
        mock_background_tasks = MagicMock()
        broadcaster = WebSocketEventBroadcaster(mock_manager, mock_background_tasks)

        payload = {"task_id": 1}

        # Act
        await broadcaster._broadcast("task_deleted", payload, None)

        # Assert
        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        broadcast_payload = call_args[0][0]
        assert broadcast_payload["type"] == "task_deleted"
        assert broadcast_payload["source_user_name"] is None

    async def test_broadcast_does_not_modify_original_payload(self):
        """Test _broadcast does not modify the original payload dict."""
        # Arrange
        mock_manager = MagicMock(spec=ConnectionManager)
        mock_manager.broadcast = AsyncMock()
        mock_background_tasks = MagicMock()
        broadcaster = WebSocketEventBroadcaster(mock_manager, mock_background_tasks)

        payload = {"task_id": 1, "task_name": "Test"}
        original_keys = set(payload.keys())

        # Act
        await broadcaster._broadcast("task_created", payload, "test-client")

        # Assert
        # Original payload should not have type and source_user_name
        assert set(payload.keys()) == original_keys
        assert "type" not in payload
        assert "source_user_name" not in payload
