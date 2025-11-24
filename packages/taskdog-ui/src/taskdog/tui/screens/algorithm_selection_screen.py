"""Algorithm selection screen for optimization."""

from datetime import datetime
from typing import Any, ClassVar

from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Input, Label, Static
from textual.widgets.option_list import Option

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.constants.ui_settings import MAX_HOURS_PER_DAY
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

    def _validate_max_hours(self, value: str) -> tuple[float | None, str | None]:
        """Validate and parse max hours input.

        Args:
            value: Input value to validate

        Returns:
            Tuple of (parsed_value, error_message).
            If valid: (float_value or None, None)
            If invalid: (None, error_message)
        """
        if not value:
            # Empty value is allowed - server will apply config default
            return None, None

        try:
            hours = float(value)
            if hours <= 0:
                return None, "Max hours must be greater than 0"
            if hours > MAX_HOURS_PER_DAY:
                return None, f"Max hours cannot exceed {MAX_HOURS_PER_DAY}"
            return hours, None
        except ValueError:
            return None, "Max hours must be a valid number"

    def _validate_start_date(self, value: str) -> tuple[datetime | None, str | None]:
        """Validate and parse start date input.

        Args:
            value: Input value to validate

        Returns:
            Tuple of (parsed_value, error_message).
            If valid: (datetime_value, None)
            If invalid: (None, error_message)
        """
        if not value:
            return None, "Start date is required"

        try:
            return dateutil_parser.parse(value, fuzzy=True), None
        except (ValueError, TypeError, OverflowError, ParserError):
            return None, "Invalid date format. Examples: today, tomorrow, 2025-12-01"

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

        # Validate max hours
        max_hours, max_hours_error = self._validate_max_hours(
            max_hours_input.value.strip()
        )
        if max_hours_error:
            self._show_validation_error(max_hours_error, max_hours_input)
            return

        # Validate start date
        start_date, start_date_error = self._validate_start_date(
            start_date_input.value.strip()
        )
        if start_date_error:
            self._show_validation_error(start_date_error, start_date_input)
            return

        # Type narrowing: start_date must be non-None (required field)
        # max_hours can be None (server will apply default)
        assert start_date is not None, "start_date validated above"

        # Submit algorithm, max_hours (can be None), and start_date
        self.dismiss((selected_algo, max_hours, start_date))
