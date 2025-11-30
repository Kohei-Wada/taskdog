"""Tests for WebSocketEventBroadcaster."""

import unittest
from unittest.mock import AsyncMock, MagicMock

from taskdog_core.application.dto.task_operation_output import TaskOperationOutput
from taskdog_core.domain.entities.task import TaskStatus
from taskdog_server.websocket.broadcaster import WebSocketEventBroadcaster
from taskdog_server.websocket.connection_manager import ConnectionManager


class TestWebSocketEventBroadcaster(unittest.TestCase):
    """Test cases for WebSocketEventBroadcaster."""

    def setUp(self):
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
            depends_on=[],
            tags=[],
            is_fixed=False,
            is_archived=False,
            actual_duration_hours=None,
            actual_daily_hours={},
        )

    def test_task_created_schedules_broadcast(self):
        """Test task_created schedules background task."""
        # Arrange
        task = self._create_task_output()
        exclude_client_id = "client-1"

        # Act
        self.broadcaster.task_created(task, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][0], self.broadcaster._broadcast)
        self.assertEqual(call_args[0][1], "task_created")
        self.assertEqual(
            call_args[0][2],
            {
                "task_id": 1,
                "task_name": "Test Task",
                "priority": 1,
                "status": "PENDING",
            },
        )
        self.assertEqual(call_args[0][3], "client-1")

    def test_task_created_without_exclude_client(self):
        """Test task_created with no exclude client."""
        # Arrange
        task = self._create_task_output()

        # Act
        self.broadcaster.task_created(task)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][3], None)

    def test_task_updated_schedules_broadcast(self):
        """Test task_updated schedules background task."""
        # Arrange
        task = self._create_task_output()
        fields = ["name", "priority"]
        exclude_client_id = "client-2"

        # Act
        self.broadcaster.task_updated(task, fields, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][0], self.broadcaster._broadcast)
        self.assertEqual(call_args[0][1], "task_updated")
        self.assertEqual(
            call_args[0][2],
            {
                "task_id": 1,
                "task_name": "Test Task",
                "updated_fields": ["name", "priority"],
                "status": "PENDING",
            },
        )
        self.assertEqual(call_args[0][3], "client-2")

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
        self.assertEqual(call_args[0][2]["updated_fields"], ["is_archived"])

    def test_task_deleted_schedules_broadcast(self):
        """Test task_deleted schedules background task."""
        # Arrange
        task_id = 123
        task_name = "Deleted Task"
        exclude_client_id = "client-3"

        # Act
        self.broadcaster.task_deleted(task_id, task_name, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][0], self.broadcaster._broadcast)
        self.assertEqual(call_args[0][1], "task_deleted")
        self.assertEqual(
            call_args[0][2],
            {
                "task_id": 123,
                "task_name": "Deleted Task",
            },
        )
        self.assertEqual(call_args[0][3], "client-3")

    def test_task_deleted_without_exclude_client(self):
        """Test task_deleted with no exclude client."""
        # Arrange
        task_id = 456
        task_name = "Another Task"

        # Act
        self.broadcaster.task_deleted(task_id, task_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][3], None)

    def test_task_status_changed_schedules_broadcast(self):
        """Test task_status_changed schedules background task."""
        # Arrange
        task = self._create_task_output(status=TaskStatus.IN_PROGRESS)
        old_status = "PENDING"
        exclude_client_id = "client-4"

        # Act
        self.broadcaster.task_status_changed(task, old_status, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][0], self.broadcaster._broadcast)
        self.assertEqual(call_args[0][1], "task_status_changed")
        self.assertEqual(
            call_args[0][2],
            {
                "task_id": 1,
                "task_name": "Test Task",
                "old_status": "PENDING",
                "new_status": "IN_PROGRESS",
            },
        )
        self.assertEqual(call_args[0][3], "client-4")

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
        self.assertEqual(call_args[0][2]["old_status"], "IN_PROGRESS")
        self.assertEqual(call_args[0][2]["new_status"], "COMPLETED")

    def test_task_notes_updated_schedules_broadcast(self):
        """Test task_notes_updated schedules background task."""
        # Arrange
        task_id = 789
        task_name = "Task with Notes"
        exclude_client_id = "client-5"

        # Act
        self.broadcaster.task_notes_updated(task_id, task_name, exclude_client_id)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][0], self.broadcaster._broadcast)
        self.assertEqual(call_args[0][1], "task_updated")
        self.assertEqual(
            call_args[0][2],
            {
                "task_id": 789,
                "task_name": "Task with Notes",
                "updated_fields": ["notes"],
            },
        )
        self.assertEqual(call_args[0][3], "client-5")

    def test_task_notes_updated_without_exclude_client(self):
        """Test task_notes_updated with no exclude client."""
        # Arrange
        task_id = 101
        task_name = "Notes Task"

        # Act
        self.broadcaster.task_notes_updated(task_id, task_name)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][3], None)

    def test_schedule_optimized_schedules_broadcast(self):
        """Test schedule_optimized schedules background task."""
        # Arrange
        scheduled_count = 5
        failed_count = 2
        algorithm = "greedy"
        exclude_client_id = "client-6"

        # Act
        self.broadcaster.schedule_optimized(
            scheduled_count, failed_count, algorithm, exclude_client_id
        )

        # Assert
        self.mock_background_tasks.add_task.assert_called_once()
        call_args = self.mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][0], self.broadcaster._broadcast)
        self.assertEqual(call_args[0][1], "schedule_optimized")
        self.assertEqual(
            call_args[0][2],
            {
                "scheduled_count": 5,
                "failed_count": 2,
                "algorithm": "greedy",
            },
        )
        self.assertEqual(call_args[0][3], "client-6")

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
            self.assertEqual(call_args[0][2]["algorithm"], algorithm)

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
        self.assertEqual(self.mock_background_tasks.add_task.call_count, 3)

    def test_broadcaster_stores_manager_and_background_tasks(self):
        """Test that broadcaster stores manager and background_tasks internally."""
        # Assert
        self.assertEqual(self.broadcaster._manager, self.mock_manager)
        self.assertEqual(self.broadcaster._background_tasks, self.mock_background_tasks)

    def test_add_background_task_schedules_task(self):
        """Test add_background_task schedules a generic background task."""

        # Arrange
        def sample_task(arg1: str, arg2: int) -> None:
            pass

        # Act
        self.broadcaster.add_background_task(sample_task, "test", 123)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            sample_task, "test", 123
        )

    def test_add_background_task_with_kwargs(self):
        """Test add_background_task with keyword arguments."""

        # Arrange
        def sample_task(name: str, value: int) -> None:
            pass

        # Act
        self.broadcaster.add_background_task(sample_task, name="test", value=456)

        # Assert
        self.mock_background_tasks.add_task.assert_called_once_with(
            sample_task, name="test", value=456
        )


class TestWebSocketEventBroadcasterBroadcast(unittest.IsolatedAsyncioTestCase):
    """Async test cases for WebSocketEventBroadcaster._broadcast method."""

    async def test_broadcast_adds_type_and_source_client_id(self):
        """Test _broadcast adds type and source_client_id to payload."""
        # Arrange
        mock_manager = MagicMock(spec=ConnectionManager)
        mock_manager.broadcast = AsyncMock()
        mock_background_tasks = MagicMock()
        broadcaster = WebSocketEventBroadcaster(mock_manager, mock_background_tasks)

        payload = {"task_id": 1, "task_name": "Test"}
        exclude_client_id = "client-1"

        # Act
        await broadcaster._broadcast("task_created", payload, exclude_client_id)

        # Assert
        mock_manager.broadcast.assert_called_once()
        call_args = mock_manager.broadcast.call_args
        broadcast_payload = call_args[0][0]
        self.assertEqual(broadcast_payload["type"], "task_created")
        self.assertEqual(broadcast_payload["source_client_id"], "client-1")
        self.assertEqual(broadcast_payload["task_id"], 1)
        self.assertEqual(broadcast_payload["task_name"], "Test")

    async def test_broadcast_with_none_exclude_client_id(self):
        """Test _broadcast with None exclude_client_id."""
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
        self.assertEqual(broadcast_payload["type"], "task_deleted")
        self.assertEqual(broadcast_payload["source_client_id"], None)

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
        await broadcaster._broadcast("task_created", payload, "client-1")

        # Assert
        # Original payload should not have type and source_client_id
        self.assertEqual(set(payload.keys()), original_keys)
        self.assertNotIn("type", payload)
        self.assertNotIn("source_client_id", payload)


if __name__ == "__main__":
    unittest.main()
