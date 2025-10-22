"""Sort order selection screen for TUI."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Label, OptionList
from textual.widgets.option_list import Option

from presentation.tui.screens.base_dialog import BaseModalDialog


class ViOptionList(OptionList):
    """OptionList with Vi-style key bindings."""

    # Add Vi-style bindings
    BINDINGS: ClassVar = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("g", "scroll_home", "Top", show=False),
        Binding("G", "scroll_end", "Bottom", show=False),
    ]

    def action_cursor_down(self) -> None:
        """Move cursor down (j key)."""
        if self.highlighted is not None:
            max_index = len(self._options) - 1
            if self.highlighted < max_index:
                self.highlighted += 1

    def action_cursor_up(self) -> None:
        """Move cursor up (k key)."""
        if self.highlighted is not None and self.highlighted > 0:
            self.highlighted -= 1

    def action_scroll_home(self) -> None:
        """Move to top (g key)."""
        self.highlighted = 0

    def action_scroll_end(self) -> None:
        """Move to bottom (G key)."""
        self.highlighted = len(self._options) - 1


class SortSelectionScreen(BaseModalDialog[str | None]):
    """Modal screen for selecting sort order."""

    BINDINGS: ClassVar = [
        ("ctrl+s", "submit", "Submit"),
        ("enter", "submit", "Submit"),
    ]

    # Sort order options with descriptions
    SORT_OPTIONS: ClassVar = [
        ("deadline", "Deadline", "Urgency-based (earlier deadline first)"),
        ("planned_start", "Planned Start", "Timeline-based (chronological order)"),
        ("priority", "Priority", "Importance-based (higher priority first)"),
        ("id", "ID", "Creation order (lower ID first)"),
    ]

    def __init__(self, current_sort: str = "deadline", *args, **kwargs):
        """Initialize the screen.

        Args:
            current_sort: Currently selected sort order
        """
        super().__init__(*args, **kwargs)
        self.current_sort = current_sort

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(id="sort-dialog"):
            yield Label("[bold cyan]Select Sort Order[/bold cyan]", id="dialog-title")
            yield Label(
                "[dim]Ctrl+S/Enter to submit, Esc to cancel, j/k to navigate[/dim]",
                id="dialog-hint",
            )

            with Vertical(id="form-container"):
                options = [
                    Option(f"{name}: {desc}", id=sort_id)
                    for sort_id, name, desc in self.SORT_OPTIONS
                ]
                yield ViOptionList(*options, id="sort-list")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Find and highlight the current sort option
        option_list = self.query_one("#sort-list", ViOptionList)
        for idx, (sort_id, _, _) in enumerate(self.SORT_OPTIONS):
            if sort_id == self.current_sort:
                option_list.highlighted = idx
                break
        else:
            # Default to first option if current sort not found
            option_list.highlighted = 0

        option_list.focus()

    def action_submit(self) -> None:
        """Submit the form."""
        option_list = self.query_one("#sort-list", ViOptionList)

        # Get selected sort order
        if option_list.highlighted is None:
            option_list.highlighted = 0

        selected_sort = self.SORT_OPTIONS[option_list.highlighted][0]

        # Submit selected sort order
        self.dismiss(selected_sort)
