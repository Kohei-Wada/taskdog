"""Tests for EventHandlerRegistry."""

from unittest.mock import MagicMock

import pytest


class TestEventHandlerRegistry:
    """Test cases for EventHandlerRegistry."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_app.api_client = MagicMock()
        self.mock_app.api_client.client_id = "test-client-id"
        self.mock_app.task_ui_manager = MagicMock()
        self.mock_app.call_later = MagicMock()
        self.mock_app.notify = MagicMock()
        # Set main_screen to None by default to avoid audit panel refresh
        self.mock_app.main_screen = None

        # Import here to avoid circular import issues
        from taskdog.tui.services.event_handler_registry import EventHandlerRegistry

        self.registry = EventHandlerRegistry(self.mock_app)

    def test_handlers_registered(self) -> None:
        """Test that all expected handlers are registered."""
        expected_handlers = [
            "connected",
            "task_created",
            "task_updated",
            "task_deleted",
            "task_status_changed",
            "schedule_optimized",
        ]
        for event_type in expected_handlers:
            assert event_type in self.registry._handlers

    def test_dispatch_connected_sets_client_id(self) -> None:
        """Test that connected event sets client ID in API client."""
        message = {"type": "connected", "client_id": "new-client-id"}
        self.registry.dispatch(message)
        self.mock_app.api_client.set_client_id.assert_called_once_with("new-client-id")

    def test_dispatch_connected_without_client_id(self) -> None:
        """Test that connected event without client_id doesn't fail."""
        message = {"type": "connected"}
        self.registry.dispatch(message)
        self.mock_app.api_client.set_client_id.assert_not_called()

    def test_dispatch_task_created_reloads_tasks(self) -> None:
        """Test that task_created event triggers task reload."""
        message = {
            "type": "task_created",
            "task_id": 1,
            "task_name": "New Task",
        }
        self.registry.dispatch(message)
        self.mock_app.call_later.assert_called_once()
        self.mock_app.notify.assert_called_once()

    def test_dispatch_task_updated_shows_fields(self) -> None:
        """Test that task_updated event shows updated fields."""
        message = {
            "type": "task_updated",
            "task_id": 1,
            "task_name": "Updated Task",
            "updated_fields": ["priority", "deadline"],
        }
        self.registry.dispatch(message)
        self.mock_app.call_later.assert_called_once()
        self.mock_app.notify.assert_called_once()

    def test_dispatch_task_deleted_shows_warning(self) -> None:
        """Test that task_deleted event shows warning notification."""
        message = {
            "type": "task_deleted",
            "task_id": 1,
            "task_name": "Deleted Task",
        }
        self.registry.dispatch(message)
        self.mock_app.call_later.assert_called_once()
        self.mock_app.notify.assert_called_once()
        # Verify warning severity
        call_args = self.mock_app.notify.call_args
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
        self.mock_app.call_later.assert_called_once()
        self.mock_app.notify.assert_called_once()

    def test_dispatch_schedule_optimized(self) -> None:
        """Test that schedule_optimized event shows optimization result."""
        message = {
            "type": "schedule_optimized",
            "scheduled_count": 5,
            "failed_count": 1,
            "algorithm": "greedy",
        }
        self.registry.dispatch(message)
        self.mock_app.call_later.assert_called_once()
        self.mock_app.notify.assert_called_once()

    def test_dispatch_unknown_event_type_ignored(self) -> None:
        """Test that unknown event types are silently ignored."""
        message = {"type": "unknown_event_type"}
        # Should not raise
        self.registry.dispatch(message)
        self.mock_app.notify.assert_not_called()

    def test_dispatch_without_type_ignored(self) -> None:
        """Test that messages without type are silently ignored."""
        message = {"data": "something"}
        # Should not raise
        self.registry.dispatch(message)
        self.mock_app.notify.assert_not_called()

    def test_source_client_id_hidden_when_same(self) -> None:
        """Test that source client ID is not shown when same as this client."""
        message = {
            "type": "task_created",
            "task_id": 1,
            "task_name": "Task",
            "source_client_id": "test-client-id",  # Same as mock_app.api_client.client_id
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

    def test_no_task_ui_manager_does_not_fail(self) -> None:
        """Test that events don't fail when task_ui_manager is None."""
        self.mock_app.task_ui_manager = None
        message = {
            "type": "task_created",
            "task_id": 1,
            "task_name": "Task",
        }
        # Should not raise
        self.registry.dispatch(message)
        self.mock_app.notify.assert_called_once()

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
        self.mock_app.notify.assert_not_called()

    def test_schedule_optimized_uses_defaults(self) -> None:
        """Test schedule_optimized with missing fields uses defaults."""
        message = {"type": "schedule_optimized"}
        self.registry.dispatch(message)
        self.mock_app.notify.assert_called_once()
        # Should not raise and should show notification

    def test_task_updated_without_fields(self) -> None:
        """Test task_updated event with no updated_fields."""
        message = {
            "type": "task_updated",
            "task_id": 1,
            "task_name": "Updated Task",
        }
        self.registry.dispatch(message)
        self.mock_app.notify.assert_called_once()

    def test_task_status_changed_without_statuses(self) -> None:
        """Test task_status_changed with missing status fields."""
        message = {
            "type": "task_status_changed",
            "task_id": 1,
            "task_name": "Task",
        }
        self.registry.dispatch(message)
        self.mock_app.notify.assert_called_once()

    def test_reload_tasks_called_with_keep_scroll_position(self) -> None:
        """Test that reload_tasks is called with keep_scroll_position=True."""
        message = {
            "type": "task_created",
            "task_id": 1,
            "task_name": "Task",
        }
        self.registry.dispatch(message)
        # Verify call_later was called with load_tasks and keep_scroll_position=True
        call_args = self.mock_app.call_later.call_args_list[0]
        assert call_args[0][0] == self.mock_app.task_ui_manager.load_tasks
        assert call_args[1]["keep_scroll_position"] is True


class TestWebSocketHandler:
    """Test cases for WebSocketHandler delegation."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.mock_app = MagicMock()
        self.mock_app.api_client = MagicMock()
        self.mock_app.api_client.client_id = "test-client-id"
        self.mock_app.task_ui_manager = MagicMock()
        self.mock_app.call_later = MagicMock()
        self.mock_app.notify = MagicMock()

    def test_handle_message_delegates_to_registry(self) -> None:
        """Test that WebSocketHandler delegates to EventHandlerRegistry."""
        from taskdog.tui.services.websocket_handler import WebSocketHandler

        handler = WebSocketHandler(self.mock_app)
        message = {"type": "connected", "client_id": "new-client"}

        handler.handle_message(message)

        self.mock_app.api_client.set_client_id.assert_called_once_with("new-client")
