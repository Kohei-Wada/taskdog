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
    BaseModalDialog[tuple[str, float, datetime, bool, bool] | None]
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
        selected_task_count: int = 0,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the screen.

        Args:
            algorithm_metadata: List of (algorithm_id, display_name, description) tuples
            selected_task_count: Number of selected tasks (0 means optimize all tasks)
        """
        super().__init__(*args, **kwargs)
        self.algorithms = algorithm_metadata
        self.selected_task_count = selected_task_count

    def compose(self) -> ComposeResult:
        """Compose the screen layout."""
        with Container(
            id="algorithm-dialog", classes="dialog-base dialog-standard"
        ) as container:
            if self.selected_task_count > 0:
                container.border_title = (
                    f"Optimize {self.selected_task_count} Selected Task(s)"
                )
            else:
                container.border_title = "Optimize All Tasks"
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

                yield Label(
                    "Max Hours per Day [red]*[/red]:",
                    classes="field-label",
                    markup=True,
                )
                yield Input(
                    placeholder="Enter max hours per day (required, e.g., 6 or 8)",
                    id="max-hours-input",
                    value="",
                    valid_empty=False,
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

                yield Label(
                    "Override existing schedules (reschedule already scheduled tasks):",
                    classes="field-label",
                )
                yield Checkbox(
                    id="force-checkbox",
                )

                yield Label(
                    "Include weekends and holidays:",
                    classes="field-label",
                )
                yield Checkbox(
                    id="include-all-days-checkbox",
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
        include_all_days_checkbox = self.query_one(
            "#include-all-days-checkbox", Checkbox
        )

        # Clear previous error
        self._clear_validation_error()

        # Validate algorithm selection
        if algorithm_select.value is Select.BLANK:
            self._show_validation_error("Please select an algorithm", algorithm_select)
            return
        selected_algo = str(algorithm_select.value)

        # Validate required fields and input validity
        if not self._validate_required(max_hours_input, "Max hours per day"):
            return
        if not self._validate_required(start_date_input, "Start date"):
            return
        if not self._validate_input(max_hours_input):
            return
        if not self._validate_input(start_date_input):
            return

        # Parse values
        max_hours = float(max_hours_input.value.strip())
        start_date = StartDateTextualValidator().parse(start_date_input.value.strip())

        # Submit algorithm, max_hours, start_date, force_override, and include_all_days
        self.dismiss(
            (
                selected_algo,
                max_hours,
                start_date,
                force_checkbox.value,
                include_all_days_checkbox.value,
            )
        )
