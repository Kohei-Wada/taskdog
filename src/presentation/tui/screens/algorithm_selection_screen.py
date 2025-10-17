"""Algorithm selection screen for optimization."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
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


class AlgorithmSelectionScreen(BaseModalDialog[str | None]):
    """Modal screen for selecting optimization algorithm."""

    ALGORITHMS: ClassVar = [
        ("greedy", "Greedy", "Front-loads tasks (default)"),
        ("balanced", "Balanced", "Even workload distribution"),
        ("backward", "Backward", "Just-in-time from deadlines"),
        ("priority_first", "Priority First", "Priority-based scheduling"),
        ("earliest_deadline", "Earliest Deadline", "EDF algorithm"),
        ("round_robin", "Round Robin", "Parallel progress on tasks"),
        ("dependency_aware", "Dependency Aware", "Critical Path Method"),
        ("genetic", "Genetic", "Evolutionary algorithm"),
        ("monte_carlo", "Monte Carlo", "Random sampling approach"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(id="algorithm-dialog"):
            yield Label("[bold cyan]Select Optimization Algorithm[/bold cyan]", id="dialog-title")
            yield Label("[dim]Press Enter to select, Esc to cancel[/dim]", id="dialog-hint")

            options = [
                Option(f"{name}: {desc}", id=algo_id) for algo_id, name, desc in self.ALGORITHMS
            ]
            yield ViOptionList(*options, id="algorithm-list")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Highlight first option by default
        option_list = self.query_one("#algorithm-list", ViOptionList)
        option_list.highlighted = 0
        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection (Enter key or double-click)."""
        option_list = self.query_one("#algorithm-list", ViOptionList)
        if option_list.highlighted is not None:
            selected = self.ALGORITHMS[option_list.highlighted][0]
            self.dismiss(selected)
