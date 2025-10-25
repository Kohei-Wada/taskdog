"""Search input widget for filtering tasks in the TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widgets import Input, Static


class SearchInput(Horizontal):
    """Search input widget with label for filtering tasks."""

    class Submitted(Message):
        """Message sent when Enter is pressed in the search input."""

    def __init__(self) -> None:
        """Initialize the search input widget."""
        super().__init__()
        self.add_class("search-container")

    def compose(self) -> ComposeResult:
        """Compose the search input with a label."""
        yield Static("🔍 Search:", classes="search-label")
        yield Input(placeholder="Type to filter tasks...", id="search-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key press in the search input.

        Args:
            event: Input submitted event
        """
        # Only handle events from our search input
        if event.input.id == "search-input":
            # Post a message to the parent screen
            self.post_message(self.Submitted())

    def clear(self) -> None:
        """Clear the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""

    @property
    def value(self) -> str:
        """Get the current search query."""
        search_input = self.query_one("#search-input", Input)
        return search_input.value

    def focus_input(self) -> None:
        """Focus the search input field."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()
