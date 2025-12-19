"""Custom footer widget with keybindings, connection status, and search input."""

from typing import TYPE_CHECKING, ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input, Static

from taskdog.tui.events import SearchQueryChanged

if TYPE_CHECKING:
    from taskdog.tui.state import ConnectionStatus

# Constants
SEARCH_INPUT_ID = "footer-search-input"


class CustomFooter(Container):
    """Custom footer with status bar and search input (Vim-style).

    Layout (2 rows):
    - Row 1 (Status bar): Keybindings (left) + Connection status (right)
    - Row 2 (Search bar): Filter chain + Search input + Result count

    Subscribes to ConnectionStatusManager for automatic updates via observer pattern.
    """

    class Submitted(Message):
        """Message sent when Enter is pressed in the search input."""

    class RefineFilter(Message):
        """Message sent when Ctrl+R is pressed to refine the filter."""

        bubble = True  # Enable message bubbling to parent widgets

    BINDINGS: ClassVar = [
        Binding(
            "ctrl+r",
            "refine_filter",
            "Refine Filter",
            show=False,
            tooltip="Refine the search filter",
        ),
    ]

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
        # Row 1: Status bar (keybindings + connection status)
        with Horizontal(id="footer-status-row"):
            yield Static(
                " [bold]q[/] Quit  [bold]a[/] Add  [bold]r[/] Refresh  [bold]S[/] Stats  [bold]?[/] Help  [bold]Ctrl+P[/] Palette",
                id="footer-keybindings",
            )
            yield Static("🔴 Offline", id="footer-connection-status")

        # Row 2: Search bar (container with filter chain, input, and result count)
        with Horizontal(id="footer-search-container"):
            yield Static("", id="footer-filter-chain")
            search_input = Input(
                placeholder="Press '/' to search, Ctrl-R to refine",
                id=SEARCH_INPUT_ID,
            )
            search_input.can_focus = True
            yield search_input
            yield Static("", id="footer-search-result")

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

    def watch_is_api_connected(self, _new_value: bool) -> None:
        """Watch for changes to API connection status."""
        self._update_connection_status()

    def watch_is_websocket_connected(self, _new_value: bool) -> None:
        """Watch for changes to WebSocket connection status."""
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

    # Search input methods

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input value changes.

        Args:
            event: Input changed event
        """
        # Only handle events from our search input
        if event.input.id == SEARCH_INPUT_ID:
            # Post SearchQueryChanged event for other widgets to react
            self.post_message(SearchQueryChanged(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key press in the search input.

        Args:
            event: Input submitted event
        """
        # Only handle events from our search input
        if event.input.id == SEARCH_INPUT_ID:
            # Post a message to the parent screen
            self.post_message(self.Submitted())

    def on_key(self, event: events.Key) -> None:
        """Handle key events.

        Args:
            event: Key event
        """
        if event.key == "ctrl+r":
            event.prevent_default()
            event.stop()
            self.action_refine_filter()

    def action_refine_filter(self) -> None:
        """Handle Ctrl+R key press to refine the filter.

        Posts a RefineFilter message to parent widget for handling.
        """
        self.post_message(self.RefineFilter())

    def clear(self) -> None:
        """Clear the search input and filter chain display."""
        search_input = self.query_one(f"#{SEARCH_INPUT_ID}", Input)
        search_input.value = ""
        self.update_result(0, 0)
        self.update_filter_chain([])

    def clear_input_only(self) -> None:
        """Clear only the search input, preserving filter chain display."""
        search_input = self.query_one(f"#{SEARCH_INPUT_ID}", Input)
        search_input.value = ""

    @property
    def value(self) -> str:
        """Get the current search query."""
        search_input = self.query_one(f"#{SEARCH_INPUT_ID}", Input)
        return search_input.value

    def focus_input(self) -> None:
        """Focus the search input field."""
        search_input = self.query_one(f"#{SEARCH_INPUT_ID}", Input)
        search_input.focus()

    def update_result(self, matched: int, total: int) -> None:
        """Update the search result count display.

        Args:
            matched: Number of matched tasks
            total: Total number of tasks
        """
        result_label = self.query_one("#footer-search-result", Static)
        if total == 0:
            # No tasks at all
            result_label.update("")
        else:
            # Always show match count for consistency
            result_label.update(f"({matched}/{total})")

    def update_filter_chain(self, filter_chain: list[str]) -> None:
        """Update the filter chain display.

        Args:
            filter_chain: List of filter queries applied in order
        """
        filter_chain_label = self.query_one("#footer-filter-chain", Static)
        if not filter_chain:
            # No filter chain
            filter_chain_label.update("")
        else:
            # Display filter chain: filter1 > filter2 > ...
            chain_display = " > ".join(f'"{f}"' for f in filter_chain)
            filter_chain_label.update(f"Filters: {chain_display} > ")
