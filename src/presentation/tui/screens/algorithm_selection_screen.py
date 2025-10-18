"""Algorithm selection screen for optimization."""

from datetime import datetime
from typing import ClassVar

from dateutil import parser as dateutil_parser
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Input, Label, OptionList, Static
from textual.widgets.option_list import Option

from presentation.tui.screens.base_dialog import BaseModalDialog
from shared.config_manager import Config


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


class AlgorithmSelectionScreen(BaseModalDialog[tuple[str, float, datetime] | None]):
    """Modal screen for selecting optimization algorithm, max hours, and start date."""

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
        ("enter", "submit", "Submit"),
    ]

    def __init__(self, config: Config, *args, **kwargs):
        """Initialize the screen.

        Args:
            config: Application configuration
        """
        super().__init__(*args, **kwargs)
        self.config = config

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(id="algorithm-dialog"):
            yield Label("[bold cyan]Optimize Schedule Settings[/bold cyan]", id="dialog-title")
            yield Label(
                "[dim]Tab to switch, Enter to submit, Esc to cancel[/dim]", id="dialog-hint"
            )

            # Error message area
            yield Static("", id="error-message")

            with Vertical(id="form-container"):
                yield Label("Algorithm:", classes="field-label")
                options = [
                    Option(f"{name}: {desc}", id=algo_id) for algo_id, name, desc in self.ALGORITHMS
                ]
                yield ViOptionList(*options, id="algorithm-list")

                yield Label("Max Hours per Day:", classes="field-label")
                yield Input(
                    placeholder="Enter max hours per day",
                    id="max-hours-input",
                    value=str(self.config.optimization.max_hours_per_day),
                )

                yield Label("Start Date:", classes="field-label")
                yield Input(
                    placeholder="Enter start date (e.g., today, tomorrow, 2025-12-01)",
                    id="start-date-input",
                    value=self._get_default_start_date(),
                )

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Highlight first option by default
        option_list = self.query_one("#algorithm-list", ViOptionList)
        option_list.highlighted = 0
        option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection (Enter key when focused on list)."""
        # When option list has enter, submit the form
        self.action_submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input fields."""
        # When Enter is pressed in any input field, submit the form
        self.action_submit()

    def _get_default_start_date(self) -> str:
        """Calculate default start date (today if weekday, otherwise next Monday).

        Returns:
            Default start date string in YYYY-MM-DD format
        """
        from datetime import timedelta

        today = datetime.now()
        # If today is a weekday, use today; otherwise use next Monday
        if today.weekday() < 5:  # Monday=0, Friday=4
            return today.strftime("%Y-%m-%d")
        # Move to next Monday
        days_until_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_monday)
        return next_monday.strftime("%Y-%m-%d")

    def action_submit(self) -> None:
        """Submit the form."""
        option_list = self.query_one("#algorithm-list", ViOptionList)
        max_hours_input = self.query_one("#max-hours-input", Input)
        start_date_input = self.query_one("#start-date-input", Input)
        error_message = self.query_one("#error-message", Static)

        # Clear previous error
        error_message.update("")

        # Get selected algorithm
        if option_list.highlighted is None:
            error_message.update("[red]Error: Please select an algorithm[/red]")
            option_list.focus()
            return

        selected_algo = self.ALGORITHMS[option_list.highlighted][0]

        # Validate and parse max hours
        max_hours_str = max_hours_input.value.strip()
        if not max_hours_str:
            error_message.update("[red]Error: Max hours per day is required[/red]")
            max_hours_input.focus()
            return

        try:
            max_hours = float(max_hours_str)
            if max_hours <= 0:
                error_message.update("[red]Error: Max hours must be greater than 0[/red]")
                max_hours_input.focus()
                return
            if max_hours > 24:
                error_message.update("[red]Error: Max hours cannot exceed 24[/red]")
                max_hours_input.focus()
                return
        except ValueError:
            error_message.update("[red]Error: Max hours must be a valid number[/red]")
            max_hours_input.focus()
            return

        # Validate and parse start date
        start_date_str = start_date_input.value.strip()
        if not start_date_str:
            error_message.update("[red]Error: Start date is required[/red]")
            start_date_input.focus()
            return

        try:
            # Parse flexible date formats using dateutil
            start_date = dateutil_parser.parse(start_date_str, fuzzy=True)
        except (ValueError, TypeError):
            error_message.update(
                "[red]Error: Invalid date format. Examples: today, tomorrow, 2025-12-01[/red]"
            )
            start_date_input.focus()
            return

        # Submit algorithm, max_hours, and start_date
        self.dismiss((selected_algo, max_hours, start_date))
