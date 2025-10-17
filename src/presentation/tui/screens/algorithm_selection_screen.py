"""Algorithm selection screen for optimization."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, OptionList
from textual.widgets.option_list import Option


class ViOptionList(OptionList):
    """OptionList with Vi-style key bindings."""

    BINDINGS: ClassVar = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("g", "scroll_home", "Top"),
        ("G", "scroll_end", "Bottom"),
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


class AlgorithmSelectionScreen(ModalScreen[str | None]):
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

    BINDINGS: ClassVar = [
        ("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(id="algorithm-dialog"):
            yield Label("[bold cyan]Select Optimization Algorithm[/bold cyan]", id="dialog-title")

            options = [
                Option(f"{name}: {desc}", id=algo_id) for algo_id, name, desc in self.ALGORITHMS
            ]
            yield ViOptionList(*options, id="algorithm-list")

            with Vertical(id="button-container"):
                yield Button("Select", variant="primary", id="select-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Highlight first option by default
        option_list = self.query_one("#algorithm-list", ViOptionList)
        option_list.highlighted = 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "select-button":
            option_list = self.query_one("#algorithm-list", ViOptionList)
            if option_list.highlighted is not None:
                selected = self.ALGORITHMS[option_list.highlighted][0]
                self.dismiss(selected)
            else:
                self.dismiss(None)
        elif event.button.id == "cancel-button":
            self.dismiss(None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection (Enter key or double-click)."""
        option_list = self.query_one("#algorithm-list", ViOptionList)
        if option_list.highlighted is not None:
            selected = self.ALGORITHMS[option_list.highlighted][0]
            self.dismiss(selected)

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(None)
