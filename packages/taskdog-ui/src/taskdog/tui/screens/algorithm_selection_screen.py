"""Algorithm selection screen for optimization."""

from datetime import datetime
from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.validation import Number
from textual.widgets import Input, Label, Static
from textual.widgets.option_list import Option

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.forms.validators import StartDateTextualValidator
from taskdog.tui.screens.base_dialog import BaseModalDialog
from taskdog.tui.widgets.vi_option_list import ViOptionList


class AlgorithmSelectionScreen(BaseModalDialog[tuple[str, float, datetime] | None]):
    """Modal screen for selecting optimization algorithm, max hours, and start date."""

    BINDINGS: ClassVar = [
        Binding(
            "ctrl+s",
            "submit",
            "Submit",
            tooltip="Submit and start optimization with selected algorithm",
        ),
        Binding(
            "ctrl+j",
            "focus_next",
            "Next field",
            priority=True,
            tooltip="Move to next form field",
        ),
        Binding(
            "ctrl+k",
            "focus_previous",
            "Previous field",
            priority=True,
            tooltip="Move to previous form field",
        ),
    ]

    def __init__(
        self,
        algorithm_metadata: list[tuple[str, str, str]],
        force_override: bool = False,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the screen.

        Args:
            algorithm_metadata: List of (algorithm_id, display_name, description) tuples
            force_override: Whether this is a force override optimization
        """
        super().__init__(*args, **kwargs)
        self.force_override = force_override
        self.algorithms = algorithm_metadata

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        # Dynamic title based on force_override mode
        title = (
            "Force Optimize Schedule Settings"
            if self.force_override
            else "Optimize Schedule Settings"
        )
        with Container(
            id="algorithm-dialog", classes="dialog-base dialog-standard"
        ) as container:
            container.border_title = title
            yield Label(
                "[dim]Ctrl+S: submit | Esc: cancel | Tab/Ctrl-j: next | Shift+Tab/Ctrl-k: previous[/dim]",
                id="dialog-hint",
            )

            # Error message area
            yield Static("", id="error-message")

            with Vertical(id="form-container"):
                yield Label("Algorithm:", classes="field-label")
                options = [
                    Option(f"{name}: {desc}", id=algo_id)
                    for algo_id, name, desc in self.algorithms
                ]
                yield ViOptionList(*options, id="algorithm-list", classes="dialog-list")

                yield Label("Max Hours per Day:", classes="field-label")
                yield Input(
                    placeholder="Enter max hours per day (typically 6-8)",
                    id="max-hours-input",
                    value="",
                    valid_empty=True,
                    validators=[Number(minimum=0.1, maximum=24)],
                )

                yield Label(
                    "Start Date [red]*[/red]:", classes="field-label", markup=True
                )
                yield Input(
                    placeholder="Enter start date (e.g., today, tomorrow, 2025-12-01)",
                    id="start-date-input",
                    value=self._get_default_start_date(),
                    validators=[StartDateTextualValidator()],
                )

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Highlight first option by default
        option_list = self.query_one("#algorithm-list", ViOptionList)
        option_list.highlighted = 0
        option_list.focus()

    def _get_default_start_date(self) -> str:
        """Calculate default start date (today if weekday, otherwise next Monday).

        Returns:
            Default start date string in YYYY-MM-DD format
        """
        from datetime import timedelta

        today = datetime.now()
        # If today is a weekday, use today; otherwise use next Monday
        if today.weekday() < 5:  # Monday=0, Friday=4
            return DateTimeFormatter.format_date_only(today)
        # Move to next Monday
        days_until_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_monday)
        return DateTimeFormatter.format_date_only(next_monday)

    def action_focus_next(self) -> None:
        """Move focus to the next field (Ctrl+J)."""
        self.focus_next()

    def action_focus_previous(self) -> None:
        """Move focus to the previous field (Ctrl+K)."""
        self.focus_previous()

    def action_submit(self) -> None:
        """Submit the form."""
        option_list = self.query_one("#algorithm-list", ViOptionList)
        max_hours_input = self.query_one("#max-hours-input", Input)
        start_date_input = self.query_one("#start-date-input", Input)

        # Clear previous error
        self._clear_validation_error()

        # Validate algorithm selection
        if option_list.highlighted is None:
            self._show_validation_error("Please select an algorithm", option_list)
            return
        selected_algo = self.algorithms[option_list.highlighted][0]

        # Validate start date (required)
        start_date_str = start_date_input.value.strip()
        if not start_date_str:
            self._show_validation_error("Start date is required", start_date_input)
            return

        # Parse values (validation handled by Textual validators)
        max_hours_str = max_hours_input.value.strip()
        max_hours = float(max_hours_str) if max_hours_str else None

        start_date_validator = StartDateTextualValidator()
        start_date = start_date_validator.parse(start_date_str)

        # Submit algorithm, max_hours (can be None), and start_date
        self.dismiss((selected_algo, max_hours, start_date))
