"""Search input widget for filtering tasks in the TUI."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import Input, Static

from presentation.tui.events import SearchQueryChanged


class SearchInput(Container):
    """Search input widget with label for filtering tasks."""

    class Submitted(Message):
        """Message sent when Enter is pressed in the search input."""

    def __init__(self) -> None:
        """Initialize the search input widget."""
        super().__init__()
        self.add_class("search-container")

    def compose(self) -> ComposeResult:
        """Compose the search input with a label."""
        with Horizontal(id="search-input-container"):
            yield Static("🔍", id="search-icon")
            yield Input(placeholder="Search for tasks...", id="search-input")
        yield Static("", id="search-result", classes="search-result")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input value changes.

        Args:
            event: Input changed event
        """
        # Only handle events from our search input
        if event.input.id == "search-input":
            # Post SearchQueryChanged event for other widgets to react
            self.post_message(SearchQueryChanged(event.value))

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
        self.update_result(0, 0)

    @property
    def value(self) -> str:
        """Get the current search query."""
        search_input = self.query_one("#search-input", Input)
        return search_input.value

    def focus_input(self) -> None:
        """Focus the search input field."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def update_result(self, matched: int, total: int) -> None:
        """Update the search result count display.

        Args:
            matched: Number of matched tasks
            total: Total number of tasks
        """
        result_label = self.query_one("#search-result", Static)
        if total == 0:
            # No tasks at all
            result_label.update("")
        else:
            # Always show match count for consistency
            result_label.update(f"({matched}/{total})")
