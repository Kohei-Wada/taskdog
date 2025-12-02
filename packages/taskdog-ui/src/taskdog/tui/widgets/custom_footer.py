"""Custom footer widget with keybindings and connection status."""

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from taskdog.tui.state import ConnectionStatus


class CustomFooter(Static):
    """Custom footer displaying essential keybindings and connection status.

    Layout:
    - Left side: Essential keybindings (q: Quit, a: Add, r: Refresh, Ctrl+P: Palette)
    - Right side: Connection status indicator (🟢 Online / 🟡 Partial / 🔴 Offline)

    Subscribes to ConnectionStatusManager for automatic updates via observer pattern.
    """

    # Reactive properties that trigger update when changed
    is_api_connected: reactive[bool] = reactive(False)
    is_websocket_connected: reactive[bool] = reactive(False)

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the custom footer."""
        super().__init__(*args, **kwargs)
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
        # Subscribe to connection status changes via observer pattern
        self.app.connection_manager.subscribe(self._on_connection_status_changed)

        # Initialize from current status
        status = self.app.connection_manager.status
        self.is_api_connected = status.is_api_connected
        self.is_websocket_connected = status.is_websocket_connected
        self._update_connection_status()

    def on_unmount(self) -> None:
        """Called when widget is unmounted from the DOM."""
        # Unsubscribe to prevent memory leaks
        self.app.connection_manager.unsubscribe(self._on_connection_status_changed)

    def _on_connection_status_changed(self, status: "ConnectionStatus") -> None:
        """Handle connection status change from ConnectionStatusManager.

        Args:
            status: New connection status
        """
        self.is_api_connected = status.is_api_connected
        self.is_websocket_connected = status.is_websocket_connected

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

    def _get_server_address(self) -> str:
        """Extract host:port from API client base URL.

        Returns:
            Server address in host:port format
        """
        base_url = self.app.api_client.base_url
        # Remove protocol (http:// or https://)
        if "://" in base_url:
            base_url = base_url.split("://", 1)[1]
        # Remove trailing slash
        return base_url.rstrip("/")

    def _update_connection_status(self) -> None:
        """Update the connection status display."""
        server_addr = self._get_server_address()

        # Determine status text and CSS class
        if self.is_api_connected and self.is_websocket_connected:
            status_text = f"🟢 Online · {server_addr}"
            status_class = "status-online"
        elif self.is_api_connected or self.is_websocket_connected:
            status_text = f"🟡 Partial · {server_addr}"
            status_class = "status-partial"
        else:
            status_text = f"🔴 Offline · {server_addr}"
            status_class = "status-offline"

        # Update connection status widget
        status_widget = self.query_one("#footer-connection-status", Static)
        status_widget.update(status_text)

        # Remove all status classes and add the current one
        status_widget.remove_class("status-online", "status-partial", "status-offline")
        status_widget.add_class(status_class)
