"""Tests for ConnectionStatusWidget."""

from unittest.mock import MagicMock, patch

import pytest

from taskdog.tui.widgets.connection_status import ConnectionStatusWidget


def create_mock_status(api: bool = False, ws: bool = False) -> MagicMock:
    """Create a mock ConnectionStatus."""
    status = MagicMock()
    status.is_api_connected = api
    status.is_websocket_connected = ws
    return status


class TestConnectionStatusWidgetInit:
    """Test cases for ConnectionStatusWidget initialization."""

    def test_adds_connection_status_class(self) -> None:
        """Test that widget adds connection-status CSS class."""
        widget = ConnectionStatusWidget()

        assert widget.has_class("connection-status")

    def test_inherits_from_static(self) -> None:
        """Test that widget inherits from Static."""
        from textual.widgets import Static

        assert issubclass(ConnectionStatusWidget, Static)

    def test_reactive_defaults_to_false(self) -> None:
        """Test that reactive properties default to False."""
        widget = ConnectionStatusWidget()

        assert widget.is_api_connected is False
        assert widget.is_websocket_connected is False


class TestConnectionStatusWidgetOnMount:
    """Test cases for on_mount method."""

    def test_subscribes_to_connection_manager(self) -> None:
        """Test that on_mount subscribes to connection status changes."""
        widget = ConnectionStatusWidget()
        mock_app = MagicMock()
        mock_status = create_mock_status()
        mock_app.connection_manager.status = mock_status
        widget._update_display = MagicMock()

        with patch.object(
            type(widget), "app", new_callable=lambda: property(lambda self: mock_app)
        ):
            widget.on_mount()

        mock_app.connection_manager.subscribe.assert_called_once_with(
            widget._on_connection_status_changed
        )

    def test_initializes_from_current_status(self) -> None:
        """Test that on_mount sets initial values from current status."""
        widget = ConnectionStatusWidget()
        mock_app = MagicMock()
        mock_status = create_mock_status(api=True, ws=True)
        mock_app.connection_manager.status = mock_status
        widget._update_display = MagicMock()

        with patch.object(
            type(widget), "app", new_callable=lambda: property(lambda self: mock_app)
        ):
            widget.on_mount()

        assert widget.is_api_connected is True
        assert widget.is_websocket_connected is True

    def test_calls_update_display(self) -> None:
        """Test that on_mount calls _update_display."""
        widget = ConnectionStatusWidget()
        mock_app = MagicMock()
        mock_status = create_mock_status()
        mock_app.connection_manager.status = mock_status
        widget._update_display = MagicMock()

        with patch.object(
            type(widget), "app", new_callable=lambda: property(lambda self: mock_app)
        ):
            widget.on_mount()

        widget._update_display.assert_called()


class TestConnectionStatusWidgetOnUnmount:
    """Test cases for on_unmount method."""

    def test_unsubscribes_from_connection_manager(self) -> None:
        """Test that on_unmount unsubscribes from connection status changes."""
        widget = ConnectionStatusWidget()
        mock_app = MagicMock()

        with patch.object(
            type(widget), "app", new_callable=lambda: property(lambda self: mock_app)
        ):
            widget.on_unmount()

        mock_app.connection_manager.unsubscribe.assert_called_once_with(
            widget._on_connection_status_changed
        )


class TestConnectionStatusWidgetStatusChanged:
    """Test cases for _on_connection_status_changed method."""

    def test_updates_reactive_properties(self) -> None:
        """Test that status change updates reactive properties."""
        widget = ConnectionStatusWidget()
        status = create_mock_status(api=True, ws=False)

        widget._on_connection_status_changed(status)

        assert widget.is_api_connected is True
        assert widget.is_websocket_connected is False

    def test_updates_both_properties_from_status(self) -> None:
        """Test that both properties are updated from status."""
        widget = ConnectionStatusWidget()
        status = create_mock_status(api=False, ws=True)

        widget._on_connection_status_changed(status)

        assert widget.is_api_connected is False
        assert widget.is_websocket_connected is True


class TestConnectionStatusWidgetWatchers:
    """Test cases for watch methods."""

    def test_watch_api_connected_calls_update_display(self) -> None:
        """Test that watching API connection triggers display update."""
        widget = ConnectionStatusWidget()
        widget._update_display = MagicMock()

        widget.watch_is_api_connected(True)

        widget._update_display.assert_called_once()

    def test_watch_websocket_connected_calls_update_display(self) -> None:
        """Test that watching WebSocket connection triggers display update."""
        widget = ConnectionStatusWidget()
        widget._update_display = MagicMock()

        widget.watch_is_websocket_connected(True)

        widget._update_display.assert_called_once()


class TestConnectionStatusWidgetUpdateDisplay:
    """Test cases for _update_display method."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        self.widget = ConnectionStatusWidget()
        # Mock methods before setting reactive properties to avoid triggering watchers
        self.widget.update = MagicMock()
        self.widget.remove_class = MagicMock()
        self.widget.add_class = MagicMock()

    def test_online_when_both_connected(self) -> None:
        """Test that status is Online when both connections are active."""
        # Set properties first (this will trigger watches)
        self.widget.is_api_connected = True
        self.widget.is_websocket_connected = True

        # Reset mocks after property assignments
        self.widget.update.reset_mock()
        self.widget.add_class.reset_mock()
        self.widget.remove_class.reset_mock()

        self.widget._update_display()

        self.widget.update.assert_called_once()
        status_text = self.widget.update.call_args[0][0]
        assert "Online" in status_text
        assert "🟢" in status_text
        self.widget.add_class.assert_called_with("status-online")

    def test_partial_when_only_api_connected(self) -> None:
        """Test that status is Partial when only API is connected."""
        self.widget.is_api_connected = True
        self.widget.is_websocket_connected = False

        self.widget._update_display()

        status_text = self.widget.update.call_args[0][0]
        assert "Partial" in status_text
        assert "🟡" in status_text
        self.widget.add_class.assert_called_with("status-partial")

    def test_partial_when_only_websocket_connected(self) -> None:
        """Test that status is Partial when only WebSocket is connected."""
        self.widget.is_api_connected = False
        self.widget.is_websocket_connected = True

        self.widget._update_display()

        status_text = self.widget.update.call_args[0][0]
        assert "Partial" in status_text
        assert "🟡" in status_text
        self.widget.add_class.assert_called_with("status-partial")

    def test_offline_when_both_disconnected(self) -> None:
        """Test that status is Offline when both connections are down."""
        self.widget.is_api_connected = False
        self.widget.is_websocket_connected = False

        self.widget._update_display()

        status_text = self.widget.update.call_args[0][0]
        assert "Offline" in status_text
        assert "🔴" in status_text
        self.widget.add_class.assert_called_with("status-offline")

    def test_removes_all_status_classes_before_adding(self) -> None:
        """Test that all status classes are removed before adding new one."""
        self.widget.is_api_connected = True
        self.widget.is_websocket_connected = True

        # Reset mocks after property assignments
        self.widget.remove_class.reset_mock()

        self.widget._update_display()

        self.widget.remove_class.assert_called_once_with(
            "status-online", "status-partial", "status-offline"
        )
