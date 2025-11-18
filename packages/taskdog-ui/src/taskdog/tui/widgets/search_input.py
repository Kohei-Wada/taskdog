"""Search input widget for filtering tasks in the TUI."""

from typing import ClassVar

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import Input, Static

from taskdog.tui.events import SearchQueryChanged

# Constants
SEARCH_INPUT_ID = "search-input"


class SearchInput(Container):
    """Search input widget with label for filtering tasks."""

    class Submitted(Message):
        """Message sent when Enter is pressed in the search input."""

    class RefineFilter(Message):
        """Message sent when Ctrl+R is pressed to refine the filter."""

        bubble = True  # Enable message bubbling to parent widgets

    BINDINGS: ClassVar = [
        Binding("ctrl+r", "refine_filter", "Refine Filter", show=False),
    ]

    def __init__(self, *args, **kwargs) -> None:
        """Initialize the search input widget."""
        super().__init__(*args, **kwargs)
        self.add_class("search-container")
        # Container itself doesn't need to be focusable; Input widget inside is focusable

    def compose(self) -> ComposeResult:
        """Compose the search input with a label."""
        yield Static("", id="filter-chain", classes="filter-chain")
        with Horizontal(id="search-input-container"):
            search_input = Input(
                placeholder="Press '/' to search tasks", id=SEARCH_INPUT_ID
            )
            search_input.can_focus = True  # Allow focus for Ctrl+J/K navigation
            yield search_input
        yield Static("", id="search-result", classes="search-result")

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

    def action_refine_filter(self) -> None:
        """Handle Ctrl+R key press to refine the filter.

        Posts a RefineFilter message to parent widget for handling.
        """
        self.post_message(self.RefineFilter())

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

    def update_filter_chain(self, filter_chain: list[str]) -> None:
        """Update the filter chain display.

        Args:
            filter_chain: List of filter queries applied in order
        """
        filter_chain_label = self.query_one("#filter-chain", Static)
        if not filter_chain:
            # No filter chain
            filter_chain_label.update("")
        else:
            # Display filter chain: filter1 > filter2 > ...
            chain_display = " > ".join(f'"{f}"' for f in filter_chain)
            filter_chain_label.update(f"Filters: {chain_display} > [Type to refine]")
