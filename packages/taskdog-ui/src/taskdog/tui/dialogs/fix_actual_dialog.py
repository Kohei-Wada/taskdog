"""Fix actual times dialog for editing actual start/end and duration."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.validation import Number
from textual.widgets import Input, Label, Static

from taskdog.formatters.date_time_formatter import DateTimeFormatter
from taskdog.tui.dialogs.form_dialog import FormDialogBase
from taskdog.tui.forms.validators import DateTimeValidator
from taskdog_core.application.dto.task_dto import TaskDetailDto
from taskdog_core.shared.constants.config_defaults import (
    DEFAULT_PLANNED_END_TIME,
    DEFAULT_PLANNED_START_TIME,
)
from taskdog_core.shared.constants.formats import DATETIME_FORMAT

if TYPE_CHECKING:
    from taskdog.infrastructure.cli_config_manager import InputDefaultsConfig


@dataclass
class FixActualFormData:
    """Data structure for fix actual form input.

    Attributes:
        actual_start: Actual start datetime string or None
        actual_end: Actual end datetime string or None
        actual_duration: Explicit duration in hours or None
        clear_start: Whether to clear actual_start
        clear_end: Whether to clear actual_end
        clear_duration: Whether to clear actual_duration
    """

    actual_start: str | None = None
    actual_end: str | None = None
    actual_duration: float | None = None
    clear_start: bool = False
    clear_end: bool = False
    clear_duration: bool = False

    def get_actual_start(self) -> datetime | None:
        """Parse actual_start to datetime."""
        if not self.actual_start:
            return None
        return datetime.strptime(self.actual_start, DATETIME_FORMAT)

    def get_actual_end(self) -> datetime | None:
        """Parse actual_end to datetime."""
        if not self.actual_end:
            return None
        return datetime.strptime(self.actual_end, DATETIME_FORMAT)


class FixActualDialog(FormDialogBase[FixActualFormData | None]):
    """Modal dialog for fixing actual start/end times and duration.

    This dialog allows editing actual_start, actual_end, and actual_duration
    for a task. It also provides clear checkboxes to remove these values.
    """

    def __init__(
        self,
        task: TaskDetailDto,
        input_defaults: "InputDefaultsConfig | None" = None,
        *args: Any,
        **kwargs: Any,
    ):
        """Initialize the dialog.

        Args:
            task: Task DTO to edit actual times for
            input_defaults: UI input completion defaults (uses hardcoded defaults if None)
        """
        super().__init__(*args, **kwargs)
        self.task_dto = task
        self._input_defaults = input_defaults

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        # Use config values or fall back to hardcoded defaults
        planned_start_time = (
            self._input_defaults.planned_start_time
            if self._input_defaults
            else DEFAULT_PLANNED_START_TIME
        )
        planned_end_time = (
            self._input_defaults.planned_end_time
            if self._input_defaults
            else DEFAULT_PLANNED_END_TIME
        )

        with Container(
            id="fix-actual-dialog", classes="dialog-base dialog-standard"
        ) as container:
            container.border_title = f"Fix Actual Times - Task #{self.task_dto.id}"
            yield Label(
                "[dim]Ctrl+S: submit | Esc: cancel | "
                "Tab/Ctrl-j: next | Shift+Tab/Ctrl-k: previous[/dim]",
                id="dialog-hint",
            )
            yield Label(
                "⚠ You are responsible for ensuring data consistency.",
                id="fix-actual-warning",
            )

            # Error message area
            yield Static("", id="error-message")

            with Vertical(id="form-container"):
                # Actual Start field
                yield Label("Actual Start:", classes="field-label")
                yield Input(
                    placeholder="Empty to clear, e.g. 2025-12-13T09:00, yesterday 9am",
                    id="actual-start-input",
                    value=DateTimeFormatter.format_datetime_for_export(
                        self.task_dto.actual_start
                    )
                    if self.task_dto.actual_start
                    else "",
                    valid_empty=True,
                    validators=[DateTimeValidator("actual start", planned_start_time)],
                )

                # Actual End field
                yield Label("Actual End:", classes="field-label")
                yield Input(
                    placeholder="Empty to clear, e.g. 2025-12-13T17:00, today 5pm",
                    id="actual-end-input",
                    value=DateTimeFormatter.format_datetime_for_export(
                        self.task_dto.actual_end
                    )
                    if self.task_dto.actual_end
                    else "",
                    valid_empty=True,
                    validators=[DateTimeValidator("actual end", planned_end_time)],
                )

                # Actual Duration field
                # Show explicit duration if set, otherwise show computed duration
                duration_value = ""
                if self.task_dto.actual_duration is not None:
                    duration_value = str(self.task_dto.actual_duration)
                elif self.task_dto.actual_duration_hours is not None:
                    duration_value = str(self.task_dto.actual_duration_hours)
                yield Label("Actual Duration (hours):", classes="field-label")
                yield Input(
                    placeholder="Empty to clear, e.g. 8, 2.5, 16 (overrides start/end)",
                    id="actual-duration-input",
                    value=duration_value,
                    valid_empty=True,
                    validators=[Number(minimum=0.01)],
                )

    def on_mount(self) -> None:
        """Called when dialog is mounted."""
        # Focus on actual start input
        actual_start_input = self.query_one("#actual-start-input", Input)
        actual_start_input.focus()

    def _submit_form(self) -> None:
        """Validate and submit the form data."""
        # Get widget values
        actual_start_input = self.query_one("#actual-start-input", Input)
        actual_end_input = self.query_one("#actual-end-input", Input)
        actual_duration_input = self.query_one("#actual-duration-input", Input)

        # Clear previous error
        self._clear_validation_error()

        # Get values
        actual_start_str = actual_start_input.value.strip()
        actual_end_str = actual_end_input.value.strip()
        actual_duration_str = actual_duration_input.value.strip()

        # Determine clear flags: clear if original had value but now empty
        clear_start = bool(self.task_dto.actual_start and not actual_start_str)
        clear_end = bool(self.task_dto.actual_end and not actual_end_str)
        # For duration: check both explicit and computed values
        had_duration = (
            self.task_dto.actual_duration is not None
            or self.task_dto.actual_duration_hours is not None
        )
        clear_duration = bool(had_duration and not actual_duration_str)

        # Check if any changes were made
        has_new_value = bool(actual_start_str or actual_end_str or actual_duration_str)
        has_clear = clear_start or clear_end or clear_duration
        if not has_new_value and not has_clear:
            self._show_validation_error("No changes made", actual_start_input)
            return

        # Validate datetime/number fields
        for input_widget in [
            actual_start_input,
            actual_end_input,
            actual_duration_input,
        ]:
            if not self._is_input_valid(input_widget):
                input_widget.focus()
                return

        # Parse datetime fields using validators registered on Input widgets
        actual_start = self._get_validator(actual_start_input, DateTimeValidator).parse(
            actual_start_str
        )
        actual_end = self._get_validator(actual_end_input, DateTimeValidator).parse(
            actual_end_str
        )

        # Validate end is not before start (when both are provided)
        if actual_start and actual_end:
            start_dt = datetime.strptime(actual_start, DATETIME_FORMAT)
            end_dt = datetime.strptime(actual_end, DATETIME_FORMAT)
            if end_dt < start_dt:
                self._show_validation_error(
                    f"End time ({actual_end}) cannot be before start time ({actual_start})",
                    actual_end_input,
                )
                return

        # Parse duration (with safety check even though validator should catch invalid input)
        actual_duration: float | None = None
        if actual_duration_str:
            try:
                actual_duration = float(actual_duration_str)
            except ValueError:
                self._show_validation_error(
                    "Invalid duration format", actual_duration_input
                )
                return

        # All validations passed - create form data
        form_data = FixActualFormData(
            actual_start=actual_start,
            actual_end=actual_end,
            actual_duration=actual_duration,
            clear_start=clear_start,
            clear_end=clear_end,
            clear_duration=clear_duration,
        )

        # Submit the form data
        self.dismiss(form_data)
