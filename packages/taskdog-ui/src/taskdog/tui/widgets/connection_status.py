"""Connection status indicator widget for TUI header."""

from typing import TYPE_CHECKING

from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from taskdog.tui.state import ConnectionStatus as ConnectionStatusData


class ConnectionStatusWidget(Static):
    """Display server connection status in the TUI header.

    Shows one of three states:
    - 🟢 Online: Both API and WebSocket are connected
    - 🟡 Partial: Only one connection is active
    - 🔴 Offline: Both connections are down

    Subscribes to ConnectionStatusManager for automatic updates via observer pattern.
    """

    # Reactive properties that trigger update when changed
    is_api_connected: reactive[bool] = reactive(False)
    is_websocket_connected: reactive[bool] = reactive(False)

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the connection status widget."""
        super().__init__(*args, **kwargs)
        self.add_class("connection-status")

    def on_mount(self) -> None:
        """Called when widget is mounted to the DOM."""
        # Subscribe to connection status changes via observer pattern
        self.app.connection_manager.subscribe(self._on_connection_status_changed)

        # Initialize from current status
        status = self.app.connection_manager.status
        self.is_api_connected = status.is_api_connected
        self.is_websocket_connected = status.is_websocket_connected
        self._update_display()

    def on_unmount(self) -> None:
        """Called when widget is unmounted from the DOM."""
        # Unsubscribe to prevent memory leaks
        self.app.connection_manager.unsubscribe(self._on_connection_status_changed)

    def _on_connection_status_changed(self, status: "ConnectionStatusData") -> None:
        """Handle connection status change from ConnectionStatusManager.

        Args:
            status: New connection status
        """
        self.is_api_connected = status.is_api_connected
        self.is_websocket_connected = status.is_websocket_connected

    def watch_is_api_connected(self, _new_value: bool) -> None:
        """Watch for changes to API connection status."""
        self._update_display()

    def watch_is_websocket_connected(self, _new_value: bool) -> None:
        """Watch for changes to WebSocket connection status."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the display based on connection status."""
        # Determine status text and CSS class
        if self.is_api_connected and self.is_websocket_connected:
            status_text = "🟢 Online"
            status_class = "status-online"
        elif self.is_api_connected or self.is_websocket_connected:
            status_text = "🟡 Partial"
            status_class = "status-partial"
        else:
            status_text = "🔴 Offline"
            status_class = "status-offline"

        # Update widget content
        self.update(status_text)

        # Remove all status classes and add the current one
        self.remove_class("status-online", "status-partial", "status-offline")
        self.add_class(status_class)
