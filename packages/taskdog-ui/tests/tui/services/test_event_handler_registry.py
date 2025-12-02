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
