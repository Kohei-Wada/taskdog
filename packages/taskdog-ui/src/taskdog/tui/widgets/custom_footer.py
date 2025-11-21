"""Custom footer widget with keybindings and connection status."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static

from taskdog.tui.state import TUIState


class CustomFooter(Static):
    """Custom footer displaying essential keybindings and connection status.

    Layout:
    - Left side: Essential keybindings (q: Quit, a: Add, r: Refresh, Ctrl+P: Palette)
    - Right side: Connection status indicator (🟢 Online / 🟡 Partial / 🔴 Offline)
    """

    # Reactive properties that trigger update when changed
    is_api_connected: reactive[bool] = reactive(False)
    is_websocket_connected: reactive[bool] = reactive(False)

    def __init__(self, state: TUIState, *args, **kwargs) -> None:
        """Initialize the custom footer.

        Args:
            state: TUI state containing connection status
        """
        super().__init__(*args, **kwargs)
        self.state = state
        self.add_class("custom-footer")

    def compose(self) -> ComposeResult:
        """Compose the footer layout.

        Returns:
            Iterable of widgets to display
        """
        with Horizontal(id="footer-container"):
            # Left side: Keybindings
            yield Static(
                " [bold]q[/] Quit  [bold]a[/] Add  [bold]r[/] Refresh  [bold]?[/] Help  [bold]Ctrl+P[/] Palette",
                id="footer-keybindings",
            )

            # Right side: Connection status
            yield Static("🔴 Offline", id="footer-connection-status")

    def on_mount(self) -> None:
        """Called when widget is mounted to the DOM."""
        # Initialize from current state
        self.is_api_connected = self.state.is_api_connected
        self.is_websocket_connected = self.state.is_websocket_connected
        self._update_connection_status()

    def watch_is_api_connected(self, new_value: bool) -> None:
        """Watch for changes to API connection status.

        Args:
            new_value: New API connection status
        """
        self._update_connection_status()

    def watch_is_websocket_connected(self, new_value: bool) -> None:
        """Watch for changes to WebSocket connection status.

        Args:
            new_value: New WebSocket connection status
        """
        self._update_connection_status()

    def _update_connection_status(self) -> None:
        """Update the connection status display."""
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

        # Update connection status widget
        status_widget = self.query_one("#footer-connection-status", Static)
        status_widget.update(status_text)

        # Remove all status classes and add the current one
        status_widget.remove_class("status-online", "status-partial", "status-offline")
        status_widget.add_class(status_class)

    def refresh_from_state(self) -> None:
        """Refresh connection status from TUIState.

        Call this method to manually update the display based on current state.
        """
        self.is_api_connected = self.state.is_api_connected
        self.is_websocket_connected = self.state.is_websocket_connected
