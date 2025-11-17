"""Connection status indicator widget for TUI header."""

from textual.reactive import reactive
from textual.widgets import Static

from taskdog.tui.state import TUIState


class ConnectionStatus(Static):
    """Display server connection status in the TUI header.

    Shows one of three states:
    - 🟢 Online: Both API and WebSocket are connected
    - 🟡 Partial: Only one connection is active
    - 🔴 Offline: Both connections are down
    """

    # Reactive properties that trigger update when changed
    is_api_connected: reactive[bool] = reactive(False)
    is_websocket_connected: reactive[bool] = reactive(False)

    def __init__(self, state: TUIState, *args, **kwargs) -> None:
        """Initialize the connection status widget.

        Args:
            state: TUI state containing connection status
        """
        super().__init__(*args, **kwargs)
        self.state = state
        self.add_class("connection-status")

    def on_mount(self) -> None:
        """Called when widget is mounted to the DOM."""
        # Initialize from current state
        self.is_api_connected = self.state.is_api_connected
        self.is_websocket_connected = self.state.is_websocket_connected
        self._update_display()

    def watch_is_api_connected(self, new_value: bool) -> None:
        """Watch for changes to API connection status.

        Args:
            new_value: New API connection status
        """
        self._update_display()

    def watch_is_websocket_connected(self, new_value: bool) -> None:
        """Watch for changes to WebSocket connection status.

        Args:
            new_value: New WebSocket connection status
        """
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

    def refresh_from_state(self) -> None:
        """Refresh connection status from TUIState.

        Call this method to manually update the display based on current state.
        """
        self.is_api_connected = self.state.is_api_connected
        self.is_websocket_connected = self.state.is_websocket_connected
