"""Algorithm selection dialog for optimization."""

from datetime import datetime
from typing import Any, ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.validation import Number
from textual.widgets import Checkbox, Input, Label, Select, Static

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.dialogs.base_dialog import BaseModalDialog
from taskdog.tui.forms.validators import StartDateTextualValidator
from taskdog.tui.widgets.vi_select import ViSelect


class AlgorithmSelectionDialog(
    BaseModalDialog[tuple[str, float | None, datetime, bool] | None]
):
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
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the screen.

        Args:
            algorithm_metadata: List of (algorithm_id, display_name, description) tuples
        """
        super().__init__(*args, **kwargs)
        self.algorithms = algorithm_metadata

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(
            id="algorithm-dialog", classes="dialog-base dialog-standard"
        ) as container:
            container.border_title = "Optimize Schedule Settings"
            yield Label(
                "[dim]Ctrl+S: submit | Esc: cancel | Tab/Ctrl-j: next | Shift+Tab/Ctrl-k: previous[/dim]",
                id="dialog-hint",
            )

            # Error message area
            yield Static("", id="error-message")

            with Vertical(id="form-container"):
                yield Label("Algorithm:", classes="field-label")
                options = [
                    (f"{name}: {desc}", algo_id)
                    for algo_id, name, desc in self.algorithms
                ]
                yield ViSelect(options, id="algorithm-select", allow_blank=False)

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

                yield Label("Force:", classes="field-label")
                yield Checkbox(
                    "Override existing schedules (reschedule already scheduled tasks)",
                    id="force-checkbox",
                )

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Focus the algorithm select (first option is auto-selected with allow_blank=False)
        algorithm_select = self.query_one("#algorithm-select", ViSelect)
        algorithm_select.focus()

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
        algorithm_select = self.query_one("#algorithm-select", ViSelect)
        max_hours_input = self.query_one("#max-hours-input", Input)
        start_date_input = self.query_one("#start-date-input", Input)
        force_checkbox = self.query_one("#force-checkbox", Checkbox)

        # Clear previous error
        self._clear_validation_error()

        # Validate algorithm selection
        if algorithm_select.value is Select.BLANK:
            self._show_validation_error("Please select an algorithm", algorithm_select)
            return
        selected_algo = str(algorithm_select.value)

        # Validate start date (required)
        start_date_str = start_date_input.value.strip()
        if not start_date_str:
            self._show_validation_error("Start date is required", start_date_input)
            return

        # Check if inputs are valid (Textual shows validation error automatically)
        if not max_hours_input.is_valid:
            max_hours_input.focus()
            return

        if not start_date_input.is_valid:
            start_date_input.focus()
            return

        # Parse values
        max_hours_str = max_hours_input.value.strip()
        max_hours = float(max_hours_str) if max_hours_str else None

        start_date_validator = StartDateTextualValidator()
        start_date = start_date_validator.parse(start_date_str)

        # Get force override value
        force_override = force_checkbox.value

        # Submit algorithm, max_hours (can be None), start_date, and force_override
        self.dismiss((selected_algo, max_hours, start_date, force_override))
