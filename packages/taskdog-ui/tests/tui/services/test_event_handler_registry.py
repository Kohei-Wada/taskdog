"""Tests for EventHandlerRegistry."""

from unittest.mock import MagicMock

import pytest


class TestEventHandlerRegistry:
    """Test cases for EventHandlerRegistry."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.notify = MagicMock()
        self.reload_tasks = MagicMock()
        self.set_client_id = MagicMock()
        self.get_client_id = MagicMock(return_value="test-client-id")

        # Import here to avoid circular import issues
        from taskdog.tui.services.event_handler_registry import EventHandlerRegistry

        self.registry = EventHandlerRegistry(
            notify=self.notify,
            reload_tasks=self.reload_tasks,
            set_client_id=self.set_client_id,
            get_client_id=self.get_client_id,
        )

    def test_handlers_registered(self) -> None:
        """Test that all expected handlers are registered."""
        expected_handlers = [
            "connected",
            "task_created",
            "task_updated",
            "task_deleted",
            "task_status_changed",
            "schedule_optimized",
            "bulk_operation_completed",
        ]
        for event_type in expected_handlers:
            assert event_type in self.registry._handlers

    def test_dispatch_connected_sets_client_id(self) -> None:
        """Test that connected event sets client ID in API client."""
        message = {"type": "connected", "client_id": "new-client-id"}
        self.registry.dispatch(message)
        self.set_client_id.assert_called_once_with("new-client-id")

    def test_dispatch_connected_without_client_id(self) -> None:
        """Test that connected event without client_id doesn't fail."""
        message = {"type": "connected"}
        self.registry.dispatch(message)
        self.set_client_id.assert_not_called()

    def test_dispatch_task_created_reloads_tasks(self) -> None:
        """Test that task_created event triggers task reload."""
        message = {
            "type": "task_created",
            "task_id": 1,
            "task_name": "New Task",
        }
        self.registry.dispatch(message)
        self.reload_tasks.assert_called_once()
        self.notify.assert_called_once()

    def test_dispatch_task_updated_shows_fields(self) -> None:
        """Test that task_updated event shows updated fields."""
        message = {
            "type": "task_updated",
            "task_id": 1,
            "task_name": "Updated Task",
            "updated_fields": ["priority", "deadline"],
        }
        self.registry.dispatch(message)
        self.reload_tasks.assert_called_once()
        self.notify.assert_called_once()

    def test_dispatch_task_deleted_shows_warning(self) -> None:
        """Test that task_deleted event shows warning notification."""
        message = {
            "type": "task_deleted",
            "task_id": 1,
            "task_name": "Deleted Task",
        }
        self.registry.dispatch(message)
        self.reload_tasks.assert_called_once()
        self.notify.assert_called_once()
        # Verify warning severity
        call_args = self.notify.call_args
        assert call_args.kwargs.get("severity") == "warning"

    def test_dispatch_task_status_changed_shows_transition(self) -> None:
        """Test that task_status_changed event shows status transition."""
        message = {
            "type": "task_status_changed",
            "task_id": 1,
            "task_name": "Task",
            "old_status": "PENDING",
            "new_status": "IN_PROGRESS",
        }
        self.registry.dispatch(message)
        self.reload_tasks.assert_called_once()
        self.notify.assert_called_once()

    def test_dispatch_schedule_optimized(self) -> None:
        """Test that schedule_optimized event shows optimization result."""
        message = {
            "type": "schedule_optimized",
            "scheduled_count": 5,
            "failed_count": 1,
            "algorithm": "greedy",
        }
        self.registry.dispatch(message)
        self.reload_tasks.assert_called_once()
        self.notify.assert_called_once()

    def test_dispatch_unknown_event_type_ignored(self) -> None:
        """Test that unknown event types are silently ignored."""
        message = {"type": "unknown_event_type"}
        # Should not raise
        self.registry.dispatch(message)
        self.notify.assert_not_called()

    def test_dispatch_without_type_ignored(self) -> None:
        """Test that messages without type are silently ignored."""
        message = {"data": "something"}
        # Should not raise
        self.registry.dispatch(message)
        self.notify.assert_not_called()

    def test_source_client_id_hidden_when_same(self) -> None:
        """Test that source client ID is not shown when same as this client."""
        message = {
            "type": "task_created",
            "task_id": 1,
            "task_name": "Task",
            "source_client_id": "test-client-id",  # Same as get_client_id() return
        }
        self.registry.dispatch(message)
        # The source should not be displayed in the notification
        result = self.registry._get_display_source(message)
        assert result is None

    def test_source_client_id_shown_when_different(self) -> None:
        """Test that source client ID is shown when different from this client."""
        message = {
            "type": "task_created",
            "task_id": 1,
            "task_name": "Task",
            "source_client_id": "other-client-id",
        }
        result = self.registry._get_display_source(message)
        assert result == "other-client-id"

    def test_source_user_name_preferred_over_client_id(self) -> None:
        """Test that source_user_name is preferred over source_client_id."""
        message = {
            "source_user_name": "John Doe",
            "source_client_id": "other-client-id",
        }
        result = self.registry._get_display_source(message)
        assert result == "John Doe"

    def test_source_user_name_empty_string_falls_back_to_client_id(self) -> None:
        """Test that empty source_user_name falls back to client_id."""
        message = {
            "source_user_name": "",
            "source_client_id": "other-client-id",
        }
        result = self.registry._get_display_source(message)
        assert result == "other-client-id"

    def test_source_user_name_none_falls_back_to_client_id(self) -> None:
        """Test that None source_user_name falls back to client_id."""
        message = {
            "source_user_name": None,
            "source_client_id": "other-client-id",
        }
        result = self.registry._get_display_source(message)
        assert result == "other-client-id"

    def test_build_task_message_with_all_params(self) -> None:
        """Test _build_task_message with all parameters."""
        msg = self.registry._build_task_message(
            action="updated",
            task_name="Test Task",
            task_id=42,
            details="priority, deadline",
            source_client_id="other-client",
        )
        assert "updated" in msg.lower()
        assert "Test Task" in msg
        # Should contain task info
        assert isinstance(msg, str)

    def test_build_task_message_minimal_params(self) -> None:
        """Test _build_task_message with minimal parameters."""
        msg = self.registry._build_task_message(
            action="added",
            task_name="Simple Task",
        )
        assert "added" in msg.lower()
        assert "Simple Task" in msg

    def test_dispatch_type_must_be_string(self) -> None:
        """Test that dispatch ignores non-string type values."""
        message = {"type": 123}  # Integer type
        self.registry.dispatch(message)
        self.notify.assert_not_called()

    def test_schedule_optimized_uses_defaults(self) -> None:
        """Test schedule_optimized with missing fields uses defaults."""
        message = {"type": "schedule_optimized"}
        self.registry.dispatch(message)
        self.notify.assert_called_once()
        # Should not raise and should show notification

    def test_task_updated_without_fields(self) -> None:
        """Test task_updated event with no updated_fields."""
        message = {
            "type": "task_updated",
            "task_id": 1,
            "task_name": "Updated Task",
        }
        self.registry.dispatch(message)
        self.notify.assert_called_once()

    def test_task_status_changed_without_statuses(self) -> None:
        """Test task_status_changed with missing status fields."""
        message = {
            "type": "task_status_changed",
            "task_id": 1,
            "task_name": "Task",
        }
        self.registry.dispatch(message)
        self.notify.assert_called_once()

    def test_dispatch_bulk_operation_completed_all_success(self) -> None:
        """Test bulk_operation_completed with all tasks succeeding."""
        message = {
            "type": "bulk_operation_completed",
            "operation": "start",
            "success_count": 3,
            "failure_count": 0,
            "task_ids": [1, 2, 3],
        }
        self.registry.dispatch(message)
        self.reload_tasks.assert_called_once()
        self.notify.assert_called_once()
        call_args = self.notify.call_args
        assert "3/3" in call_args[0][0]
        assert call_args.kwargs.get("severity") == "information"

    def test_dispatch_bulk_operation_completed_with_failures(self) -> None:
        """Test bulk_operation_completed with some failures shows warning."""
        message = {
            "type": "bulk_operation_completed",
            "operation": "archive",
            "success_count": 2,
            "failure_count": 1,
            "task_ids": [1, 2, 3],
        }
        self.registry.dispatch(message)
        self.reload_tasks.assert_called_once()
        self.notify.assert_called_once()
        call_args = self.notify.call_args
        assert "2/3" in call_args[0][0]
        assert call_args.kwargs.get("severity") == "warning"

    def test_dispatch_bulk_operation_completed_defaults(self) -> None:
        """Test bulk_operation_completed with missing fields uses defaults."""
        message = {"type": "bulk_operation_completed"}
        self.registry.dispatch(message)
        self.notify.assert_called_once()
        call_args = self.notify.call_args
        assert "0/0" in call_args[0][0]
        assert "unknown" in call_args[0][0]

    def test_reload_routes_through_request_reload_funnel(self) -> None:
        """Reloads are delegated to the app's single debounced reload funnel."""
        message = {
            "type": "task_created",
            "task_id": 1,
            "task_name": "Task",
        }
        self.registry.dispatch(message)
        self.reload_tasks.assert_called_once_with()


class TestWebSocketHandler:
    """Test cases for WebSocketHandler delegation."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.notify = MagicMock()
        self.reload_tasks = MagicMock()
        self.set_client_id = MagicMock()
        self.get_client_id = MagicMock(return_value="test-client-id")

    def test_handle_message_delegates_to_registry(self) -> None:
        """Test that WebSocketHandler delegates to EventHandlerRegistry."""
        from taskdog.tui.services.websocket_handler import WebSocketHandler

        handler = WebSocketHandler(
            notify=self.notify,
            reload_tasks=self.reload_tasks,
            set_client_id=self.set_client_id,
            get_client_id=self.get_client_id,
        )
        message = {"type": "connected", "client_id": "new-client"}

        handler.handle_message(message)

        self.set_client_id.assert_called_once_with("new-client")
